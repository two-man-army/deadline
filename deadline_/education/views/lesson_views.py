"""
    Views that are directly related to the Lesson model
"""
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from decorators import fetch_models
from education.permissions import IsTeacher, IsEnrolledOnCourseOrIsTeacher, IsTeacherOfCourse
from education.serializers import LessonSerializer
from education.models import Course, Lesson, Homework
from views import BaseManageView


# DELETE /education/course/{course_id}/lessons/{lesson_id}
class CourseLessonDeleteView(APIView):
    permission_classes = (IsAuthenticated, IsTeacherOfCourse)
    model_classes = (Course, Lesson)
    main_class = Course

    @fetch_models
    def delete(self, request, course: Course, lesson: Lesson, *args, **kwargs):
        if not course.is_under_construction:
            return Response(status=400, data={'error': f'Cannot remove a Lesson from a Course when the Course is locked!'})
        if lesson not in course.lessons.all():
            return Response(status=404, data={'error': f'Lesson {lesson.id} is not present in course {course.id}'})

        course.remove_lesson(lesson)

        return Response(status=204)


# /education/course/{course_id}/lesson
class LessonCreateView(CreateAPIView):
    """
    Creates a new Lesson for a given Course
    """
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated, IsTeacherOfCourse, )
    model_classes = (Course, )
    main_class = Course

    @fetch_models
    def create(self, request, course, *args, **kwargs):
        response = self.validate_data(course)
        if response is not None:
            return response  # there has been an error in validation

        self.request.data['course'] = kwargs.get('course_pk')
        ser_data, response = self.create_lesson_and_homework()
        if response is not None:
            return response

        return Response(ser_data, status=201, headers=self.get_success_headers(ser_data))

    def validate_data(self, course) -> Response or None:
        """ Validate the given course_pk and the user's association to it"""
        if not course.is_under_construction:
            return Response(data={'error': 'Cannot create a Lesson in a Course that is not under construction!'},
                            status=400)
        if not any(teacher.id == self.request.user.id for teacher in course.teachers.all()):
            return Response(data={'error': 'You do not have permission to create Course Lessons!'}, status=403)

        return None

    def create_lesson_and_homework(self):
        ser = self.get_serializer(data=self.request.data)
        if not ser.is_valid():
            return None, Response(data={'error': f'Error while creating Lesson: {ser.errors}'}, status=400)
        lesson = self.perform_create(ser)

        if self.request.data.get('create_homework', default=False):
            # create a Homework object for the given Lesson
            Homework.objects.create(lesson=lesson, is_mandatory=True)  # homework should be mandatory by default

        return ser.data, None

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
        if str(lesson.course_id) != kwargs.get('course_pk', -1):
            return Response(status=400)

        serializer = self.get_serializer(lesson)
        response_data = serializer.data
        lesson_homework = lesson.homework_set.first()
        if lesson_homework is not None:
            response_data['homework'] = {'task_count': lesson_homework.homeworktask_set.count()}
        response_data['is_completed'] = lesson.is_completed_by(request.user)

        return Response(response_data)


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

            can_lock, err_msg = lesson.can_lock()
            if not can_lock:
                return Response(data={'error': err_msg}, status=400)

            if request.user != lesson.course.main_teacher:
                return Response(data={'error': "Only the Course's main teacher can lock a course!"}, status=400)

            lesson.lock_for_construction()
            serializer = self.get_serializer(lesson)
            return Response(serializer.data)

        return super().patch(request, *args, **kwargs)


# /education/course/{course_id}/lesson/{lesson_id}
class LessonManageView(BaseManageView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'GET': LessonDetailsView.as_view,
        'PATCH': LessonEditView.as_view,
        'DELETE': CourseLessonDeleteView.as_view
    }
