from django.shortcuts import render

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from education.permissions import IsTeacher
from education.serializers import CourseSerializer


# /education/course
class CourseCreateView(CreateAPIView):
    """
    Creates a new Course
    """
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated, IsTeacher, )

    def perform_create(self, serializer):
        serializer.save(teachers=[self.request.user])