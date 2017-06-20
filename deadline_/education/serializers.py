from rest_framework import serializers

from education.models import Course, HomeworkTaskDescription
from challenges.models import User
from accounts.serializers import UserSerializer


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('name', 'difficulty', 'languages')


class HomeworkTaskDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkTaskDescription
        exclude = ('id', )
