"""
    Views that are directly related to the Course model
"""
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from challenges.models import Language
from decorators import fetch_models
from education.permissions import IsTeacher, IsEnrolledOnCourseOrIsTeacher, IsTeacherOfCourse
from education.serializers import CourseSerializer
from education.models import Course
from errors import FetchError
from helpers import fetch_models_by_pks
from views import BaseManageView


# /education/course
class CourseCreateView(CreateAPIView):
    """
    Creates a new Course
    """
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsTeacher)

    def post(self, request, *args, **kwargs):
        request.data['main_teacher'] = self.request.user.id
        return super().post(request, *args, **kwargs)


# /education/course/{course_id}
class CourseDetailsView(RetrieveAPIView):
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsEnrolledOnCourseOrIsTeacher)
    queryset = Course.objects.all()


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

        if 'is_under_construction' in request.data:
            is_under_construction = request.data['is_under_construction']

            if is_under_construction:  # Cannot unlock a Lesson
                err_msg = 'Cannot unlock a Course'
                if not course.is_under_construction:
                    err_msg = 'Cannot unlock an already locked Course'
                return Response(data={'error': err_msg}, status=400)

            if not course.is_under_construction:  # Cannot lock a course twice
                return Response(data={'error': 'Cannot lock an already locked Course'}, status=400)

            if not course.can_lock():
                return Response(data={'error': 'Cannot lock the Course for some reason'}, status=400)

            if not course.is_main_teacher(request.user):
                return Response(data={'error': 'Only the main teacher can lock the Course'}, status=400)

            course.lock_for_construction()
            serializer = self.get_serializer(course)
            return Response(serializer.data)

        if 'main_teacher' in request.data and request.user != course.main_teacher:
            return Response(data={'error': 'Only the main teacher can set a new main teacher'}, status=400)

        return super().patch(request, *args, **kwargs)

    def get_object(self):
        """ Query for the object only once """
        if not hasattr(self, 'obj'):
            self.obj = super().get_object()
        return self.obj


# /education/course/{course_id}
class CourseManageView(BaseManageView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'GET': CourseDetailsView.as_view,
        'PATCH': CourseEditView.as_view
    }


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
            language = Language.objects.get(id=request.data.get('language', -1))
        except Language.DoesNotExist as e:
            return Response(status=400, data={'error': str(e)})

        if not course.is_under_construction:
            return Response(status=400, data={'error': f'Cannot add a Language to a Course when the Course is locked!'})
        if language in course.languages.all():
            return Response(status=400, data={'error': f'Language {language.id} is already in course {course.id}'})

        course.languages.add(language)
        return Response(status=201)
