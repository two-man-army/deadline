import collections

from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse

from errors import FetchError
from helpers import fetch_models_by_pks
from challenges.models import Language
from education.permissions import IsTeacher, IsEnrolledOnCourseOrIsTeacher, IsTeacherOfCourse
from education.serializers import CourseSerializer, HomeworkTaskSerializer, LessonSerializer, TaskSubmissionSerializer
from education.models import Course, Lesson, HomeworkTask, HomeworkTaskTest, Homework
from education.helpers import create_task_test_files
from challenges.tasks import run_homework_grader_task
from decorators import fetch_models


# /education/course
class CourseCreateView(CreateAPIView):
    """
    Creates a new Course
    """
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(teachers=[self.request.user])


# /education/course/{course_id}
class CourseDetailsView(RetrieveAPIView):
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsEnrolledOnCourseOrIsTeacher)
    queryset = Course.objects.all()
    # TODO: Maybe add a LimitedCourseDetails view


# PATCH /education/course/{course_id}
class CourseEditView(UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsTeacherOfCourse)

    def patch(self, request, *args, **kwargs):
        request.data.pop('languages', None)  # you cannot edit the languages from here
        course: Course = self.get_object()
        if not course.is_under_construction:
            return Response(data={'error': 'Cannot edit anything on a locked Course'}, status=400)

        # TODO: add/remove language
        if 'is_under_construction' in request.data:
            is_under_construction = request.data['is_under_construction']

            if is_under_construction:  # Cannot unlock a Lesson
                err_msg = 'Cannot unlock a Course'
                if not course.is_under_construction:
                    err_msg = 'Cannot unlock an already locked Course'
                return Response(data={'error': err_msg}, status=400)

            if not course.is_under_construction:  # Cannot lock a course twice
                return Response(data={'error': 'Cannot lock an already locked Course'}, status=400)

            # TODO: Assure that the user is the main Teacher before lock
            course.lock_for_construction()
            serializer = self.get_serializer(course)
            return Response(serializer.data)

        return super().patch(request, *args, **kwargs)

    def get_object(self):
        """ Query for the object only once """
        if not hasattr(self, 'obj'):
            self.obj = super().get_object()
        return self.obj


# /education/course/{course_id}
class CourseManageView(APIView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'GET': CourseDetailsView.as_view,
        'PATCH': CourseEditView.as_view
    }

    def dispatch(self, request, *args, **kwargs):
        if request.method in self.VIEWS_BY_METHOD:
            return self.VIEWS_BY_METHOD[request.method]()(request, *args, **kwargs)

        return HttpResponse(status=404)


# DELETE /education/course/{course_id}/language/{language_id}
class CourseLanguageDeleteView(APIView):
    """ Removes a Language from a given Course """
    permission_classes = (IsAuthenticated, IsTeacherOfCourse)
    model_classes = (Course, Language)
    main_class = Course

    @fetch_models
    def delete(self, request, course: Course, language: Language, *args, **kwargs):
        if not course.is_under_construction:
            return Response(status=400, data={'error': f'Cannot remove a Language from a Course when the Course is locked!'})
        if language not in course.languages.all():
            return Response(status=400, data={'error': f'Language {language.id} is not present in course {course.id}'})

        course.languages.remove(language)
        return Response(status=204)


# POST /education/course/{course_id}/language
class CourseLanguageAddView(APIView):
    """ Adds a Language to a given Course """
    permission_classes = (IsAuthenticated, IsTeacherOfCourse)
    model_classes = (Course, )
    main_class = Course

    @fetch_models
    def post(self, request, course: Course, *args, **kwargs):
        try:
            language, *_ = fetch_models_by_pks({Language: request.data.get('language', -1)})
        except FetchError as e:
            return Response(status=404, data={'error': str(e)})

        if not course.is_under_construction:
            return Response(status=400, data={'error': f'Cannot add a Language to a Course when the Course is locked!'})
        if language in course.languages.all():
            return Response(status=400, data={'error': f'Language {language.id} is already in course {course.id}'})

        course.languages.add(language)
        return Response(status=201)


# /education/course/{course_id}/lesson
class LessonCreateView(CreateAPIView):
    """
    Creates a new Lesson for a given Course
    """
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsTeacher, )

    def create(self, request, *args, **kwargs):
        validation = self.validate_data(course_pk=kwargs.get('course_pk'))
        if isinstance(validation, Response):
            return validation  # there has been an error in validation

        self.request.data['course'] = kwargs.get('course_pk')
        ser = self.get_serializer(data=self.request.data)
        if not ser.is_valid():
            return Response(data={'error': f'Error while creating Lesson: {ser.errors}'},
                            status=400)
        lesson = self.perform_create(ser)
        headers = self.get_success_headers(ser.data)

        if request.data.get('create_homework', default=False):
            # create a Homework object for the given Lesson
            Homework.objects.create(lesson=lesson, is_mandatory=True)  # homework should be mandatory by default

        return Response(ser.data, status=201, headers=headers)

    def validate_data(self, course_pk) -> Response or Course:
        """ Validate the given course_pk and the user's association to it"""
        try:
            course = Course.objects.get(id=course_pk)
        except Course.DoesNotExist:
            return Response(data={'error': 'Course with ID {} does not exist.'.format(course_pk)},
                            status=400)

        if not course.is_under_construction:
            return Response(data={'error': 'Cannot create a Lesson in a Course that is not under construction!'},
                            status=400)
        if not any(teacher.id == self.request.user.id for teacher in course.teachers.all()):
            return Response(data={'error': 'You do not have permission to create Course Lessons!'}, status=403)

        return course

    def perform_create(self, serializer):
        return serializer.save()


# /education/course/{course_id}/lesson/{lesson_id}
class LessonDetailsView(RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsEnrolledOnCourseOrIsTeacher)

    def retrieve(self, request, *args, **kwargs):
        """ Attach a couple of fields to the response
            - A short object for the homework, homework: {task_count: 2}, denoting the number of homeworktasks
            - is_completed - indicating if the current user has completed the lesson
        """
        lesson = self.get_object()
        if lesson.course_id != kwargs.get('course_pk', -1):
            return Response(status=400)

        serializer = self.get_serializer(lesson)
        response_data = serializer.data
        lesson_homework = lesson.homework_set.first()
        if lesson_homework is not None:
            response_data['homework'] = {'task_count': lesson_homework.homeworktask_set.count()}
        response_data['is_completed'] = lesson.is_completed_by(request.user)

        return Response(response_data)


# TODO: Add main Teacher to Course and Lesson, allow only those to Lock
class LessonEditView(UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsTeacherOfCourse)

    def patch(self, request, *args, **kwargs):
        request.data.pop('course', None)  # updating the course is not possible

        if 'is_under_construction' in request.data:
            is_under_construction = request.data['is_under_construction']
            lesson = self.get_object()

            if is_under_construction:  # Cannot unlock a Lesson
                err_msg = 'Cannot unlock a Lesson'
                if not lesson.is_under_construction:
                    err_msg = 'Cannot unlock an already locked Lesson'
                return Response(data={'error': err_msg}, status=400)

            if not lesson.is_under_construction:  # Cannot lock a lesson twice
                return Response(data={'error': 'Cannot lock an already locked Lesson'}, status=400)

            # TODO: Assure that the user is the main Teacher before lock
            if not lesson.can_lock():
                return Response(data={'error': 'Cannot lock the Lesson due to some reason.'}, status=400)

            lesson.lock_for_construction()
            serializer = self.get_serializer(lesson)
            return Response(serializer.data)

        return super().patch(request, *args, **kwargs)


# /education/course/{course_id}/lesson/{lesson_id}
class LessonManageView(APIView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'GET': LessonDetailsView.as_view,
        'PATCH': LessonEditView.as_view
    }

    def dispatch(self, request, *args, **kwargs):
        if request.method in self.VIEWS_BY_METHOD:
            return self.VIEWS_BY_METHOD[request.method]()(request, *args, **kwargs)

        return HttpResponse(status=404)


# POST /education/course/{course_id}/lesson/{lesson_id}/homework_task
class HomeworkTaskCreateView(CreateAPIView):
    """ Creates a new HomeworkTask for the given Lesson of a Course """
    serializer_class = HomeworkTaskSerializer
    permission_classes = (IsAuthenticated, IsTeacher, )

    def create(self, request, *args, **kwargs):
        validation = self.validate_data(course_pk=kwargs.get('course_pk'),
                                        lesson_pk=kwargs.get('lesson_pk'))
        if isinstance(validation, Response):
            return validation  # there has been an error in validation

        _, lesson = validation
        self.request.data['homework'] = lesson.homework_set.first().id
        ser = self.get_serializer(data=self.request.data)
        if not ser.is_valid():
            return Response(data={'error': f'Error while creating Homework Task: {ser.errors}'},
                            status=400)
        self.perform_create(ser)
        headers = self.get_success_headers(ser.data)

        return Response(ser.data, status=201, headers=headers)

    def validate_data(self, course_pk, lesson_pk) -> Response or tuple():
        """ Validate the given course_pk, lesson_pk and their association """
        try:
            objects = fetch_models_by_pks({
                Course: course_pk,
                Lesson: lesson_pk
            })
        except FetchError as e:
            return Response(data={'error': str(e)},
                            status=404)

        course, lesson = objects

        if lesson.course_id != course.id:
            return Response(data={'error': 'Lesson with ID {} does not belong to Course with ID {}'
                            .format(lesson_pk, course_pk)},
                            status=400)

        # validate that the current User is part of the teachers for the Course
        if not any(teacher.id == self.request.user.id for teacher in course.teachers.all()):
            return Response(data={'error': 'You do not have permission to create Course Homework!'}, status=403)

        if not course.is_under_construction:
            # the course is finished and you cannot add further homework tasks
            return Response(data={
                'error': 'The course is no longer under construction and as such you cannot create a new HomeworkTask'},
                status=400)
        if not lesson.is_under_construction:
            # the course is finished and you cannot add further homework tasks
            return Response(data={
                'error': 'The lesson is no longer under construction and as such you cannot create a new HomeworkTask'},
                status=400)

        return course, lesson


# POST /education/course/{course_id}/lesson/{lesson_id}/homework_task/
class HomeworkTaskTestCreateView(APIView):
    """
    Creates a Test case for a HomeworkTask
    """
    permission_classes = (IsAuthenticated, IsTeacher, )

    def post(self, request, *args, **kwargs):
        try:
            objects = fetch_models_by_pks({
                Course: kwargs.get('course_pk', ''),
                Lesson: kwargs.get('lesson_pk', ''),
                HomeworkTask: kwargs.get('task_pk', '')
            })
        except FetchError as e:
            return Response(status=404, data={'error': str(e)})

        course, lesson, task = objects

        # TODO: move to validate method
        if self.request.user not in course.teachers.all():
            return Response(status=403, data={'error': f'You do not have permission to create Homework Task Tests!'})
        if not course.is_under_construction:
            return Response(status=403, data={'error': f'You cannot add tests as the Course is not under construction'})
        if not lesson.is_under_construction:
            return Response(status=403, data={'error': f'You cannot add tests as the Lesson is not under construction'})
        if not task.is_under_construction:
            return Response(status=403, data={'error': f'You cannot add tests as the Task is not under construction'})
        if lesson.course != course:
            return Response(status=403, data={'error': f'Lesson {lesson.id} does not belong to Course {course.id}'})
        if lesson != task.homework.lesson:
            return Response(status=403, data={'error': f'Task {task.id} does not belong to Lesson {lesson.id}'})

        test_input, test_output = request.data.get('input', ''), request.data.get('output', '')
        input_file_path, output_file_path = create_task_test_files(
            task_tests_dir=task.get_absolute_test_files_path(),
            test_number=task.test_case_count + 1,
            input=test_input, output=test_output
        )

        HomeworkTaskTest.objects.create(
            input_file_path=input_file_path, output_file_path=output_file_path, task=task,
            consecutive_number=task.test_case_count + 1
        )
        # TODO: Consecutive_number generation in helper method

        task.test_case_count += 1
        task.save()

        return Response(status=201)


class TaskSubmissionCreateView(CreateAPIView):
    serializer_class = TaskSubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        objects, is_valid, response = self.validate_data(
            user=request.user,
            course_pk=kwargs.get('course_pk'),
            lesson_pk=kwargs.get('lesson_pk'),
            task_pk=kwargs.get('task_pk'),
            language_pk=request.data.get('language', ''))

        if not is_valid:
            return response # there has been an error in validation
        # TODO: Check supported languages
        course, lesson, task, language = objects

        self.request.data['author'] = self.request.user.id
        self.request.data['task'] = task.id
        ser = self.get_serializer(data=self.request.data)
        if not ser.is_valid():
            return Response(data={'error': f'Error while creating Homework Task: {ser.errors}'},
                            status=400)
        submission = self.perform_create(ser)

        run_homework_grader_task(test_case_count=task.test_case_count,
                                 abs_test_files_path=task.get_absolute_test_files_path(),
                                 code=self.request.data['code'],
                                 lang=language.name, submission_id=submission.id)

        headers = self.get_success_headers(ser.data)

        return Response(ser.data, status=201, headers=headers)

    def validate_data(self, user, course_pk, lesson_pk, task_pk, language_pk) -> (['Models'], bool, Response):
        # TODO: Try/catches can be refactored to a universal helper method
        try:
            fetched_objects = fetch_models_by_pks({
                Course: course_pk,
                Lesson: lesson_pk,
                HomeworkTask: task_pk,
                Language: language_pk
            })
        except FetchError as e:
            return [], False, Response(data={'error': str(e)},
                                       status=400)
        course, lesson, task, language = fetched_objects
        if not IsEnrolledOnCourseOrIsTeacher.can_access(course, user):
            return [], False, Response(data={'error': f'You do not have permission to interact with that Course.'},
                                       status=403)

        if language not in task.supported_languages.all():
            return [], False, Response(data={'error': f'HomeworkTask {task_pk} does not support Language {language_pk}.'},
                            status=400)
        if task.homework.lesson != lesson:
            return [], False, Response(data={'error': f'Task with ID {task_pk} does not belong to Lesson with ID {lesson_pk}'},
                            status=400)
        if lesson.course != course:
            return [], False, Response(data={'error': f'Lesson with ID {lesson_pk} does not belong to Course with ID {course_pk}.'},
                            status=400)

        # Everything below should not be able to happen for a normal user,
        # as they would not be able to enroll on the Course to access this URL
        # FIXME?: Maybe allow Teacher to submit while
        if course.is_under_construction:
            return [], False, Response(data={'error': f'Cannot submit HWSubmission while Course is under construction!.'},
                            status=400)
        if lesson.is_under_construction:
            return [], False, Response(data={'error': f'Cannot submit HWSubmission while Lesson is under construction!.'},
                            status=400)
        if task.is_under_construction:
            return [], False, Response(data={'error': f'Cannot submit HWSubmission while HWTask is under construction!.'},
                            status=400)

        return [course, lesson, task, language], True, None

    def perform_create(self, serializer):
        return serializer.save()
