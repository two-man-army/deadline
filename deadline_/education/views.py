from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse

from education.permissions import IsTeacher
from education.serializers import CourseSerializer, HomeworkTaskSerializer, LessonSerializer
from education.models import Course, Lesson, HomeworkTask, HomeworkTaskTest
from education.helpers import create_task_test_files


# /education/course
class CourseCreateView(CreateAPIView):
    """
    Creates a new Course
    """
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsTeacher, )

    def perform_create(self, serializer):
        serializer.save(teachers=[self.request.user])


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
        self.perform_create(ser)
        headers = self.get_success_headers(ser.data)

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


# /education/course/{course_id}/lesson
class LessonManageView(APIView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'POST': LessonCreateView.as_view
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
            course = Course.objects.get(id=course_pk)
        except Course.DoesNotExist:
            return Response(data={'error': 'Course with ID {} does not exist.'.format(course_pk)},
                            status=400)
        try:
            lesson = Lesson.objects.get(id=lesson_pk)
        except Lesson.DoesNotExist:
            return Response(data={'error': 'Lesson with ID {} does not exist.'.format(lesson_pk)},
                            status=400)

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


# POST /education/course/{course_id}/lesson/{lesson_id}/homework_task/{task_id}
class HomeworkTaskTestCreateView(APIView):
    permission_classes = (IsAuthenticated, IsTeacher, )

    def post(self, request, *args, **kwargs):
        course_id, lesson_id, task_id = (kwargs.get('course_pk', ''), kwargs.get('lesson_pk', ''), kwargs.get('task_pk', ''))
        problematic_model, problematic_id = None, None
        try:
            course = Course.objects.get(id=course_id)
            lesson = Lesson.objects.get(id=lesson_id)
            task = HomeworkTask.objects.get(id=task_id)
        except Course.DoesNotExist:
            problematic_model = 'Course'
            problematic_id = course_id
        except Lesson.DoesNotExist:
            problematic_model = 'Lesson'
            problematic_id = lesson_id
        except HomeworkTask.DoesNotExist:
            problematic_model = 'Homework Task'
            problematic_id = task_id

        # TODO: move to validate method
        if problematic_model is not None:  # error while fetching models
            return Response(status=404, data={'error': f'No {problematic_model} with ID {problematic_id}'})
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
            course_name=course.name, lesson_number=lesson.lesson_number,
            task_number=task.consecutive_number, input=test_input, output=test_output
        )

        task_test = HomeworkTaskTest.objects.create(
            input_file_path=input_file_path, output_file_path=output_file_path, task=task,
            consecutive_number=task.test_case_count + 1
        )
        # TODO: Consecutive_number generation in helper method

        task.test_case_count += 1
        task.save()

        return Response(status=201)
