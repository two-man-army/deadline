from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.http import HttpResponse

from helpers import fetch_models_by_pks
from challenges.models import Language
from education.permissions import IsTeacher, IsEnrolledOnCourseOrIsTeacher
from education.serializers import CourseSerializer, HomeworkTaskSerializer, LessonSerializer, TaskSubmissionSerializer
from education.models import Course, Lesson, HomeworkTask, HomeworkTaskTest, Homework
from education.helpers import create_task_test_files
from challenges.tasks import run_homework_grader_task


# /education/course
class CourseCreateView(CreateAPIView):
    """
    Creates a new Course
    """
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsTeacher, )

    def perform_create(self, serializer):
        serializer.save(teachers=[self.request.user])


# /education/course/{course_id}
class CourseDetailsView(RetrieveAPIView):
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsEnrolledOnCourseOrIsTeacher)
    queryset = Course.objects.all()
    # TODO: Maybe add a LimitedCourseDetails view


# /education/course/{course_id}
class CourseManageView(APIView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'GET': CourseDetailsView.as_view
    }

    def dispatch(self, request, *args, **kwargs):
        if request.method in self.VIEWS_BY_METHOD:
            return self.VIEWS_BY_METHOD[request.method]()(request, *args, **kwargs)

        return HttpResponse(status=404)


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
        serializer = self.get_serializer(lesson)
        response_data = serializer.data
        lesson_homework = lesson.homework_set.first()
        if lesson_homework is not None:
            response_data['homework'] = {'task_count': lesson_homework.homeworktask_set.count()}
        response_data['is_completed'] = lesson.is_completed_by(request.user)

        return Response(response_data)
from rest_framework.generics import UpdateAPIView


class LessonEditView(UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsEnrolledOnCourseOrIsTeacher)

    def patch(self, request, *args, **kwargs):

        # is_under_construction = request.data.get('is_under_construction', True)
        # if is_under_construction:
        #     # TODO: LOCK
        #     pass
        # del request.data['course']  # updating the course is not possible
        # del request.data['is_under_construction']  # Can only be modified once
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
        objects, are_valid, err_msg = fetch_models_by_pks({
            Course: course_pk,
            Lesson: lesson_pk
        })
        if not are_valid:
            return Response(data={'error': err_msg},
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
        objects, are_valid, err_msg = fetch_models_by_pks({
            Course: kwargs.get('course_pk', ''),
            Lesson: kwargs.get('lesson_pk', ''),
            HomeworkTask: kwargs.get('task_pk', '')
        })
        if not are_valid:
            return Response(status=404, data={'error': err_msg})

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
        fetched_objects, are_valid, err_msg = fetch_models_by_pks({
            Course: course_pk,
            Lesson: lesson_pk,
            HomeworkTask: task_pk,
            Language: language_pk
        })
        if not are_valid:
            return [], False, Response(data={'error': err_msg},
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
