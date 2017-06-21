from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from education.permissions import IsTeacher
from education.serializers import CourseSerializer, HomeworkTaskSerializer
from education.models import Course, Lesson


# /education/course
class CourseCreateView(CreateAPIView):
    """
    Creates a new Course
    """
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsTeacher, )

    def perform_create(self, serializer):
        serializer.save(teachers=[self.request.user])


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
        """ Validate the given challenge_id, submission_id and their association """
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

        return course, lesson
