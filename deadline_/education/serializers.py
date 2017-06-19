from rest_framework import serializers

from education.models import Course
from challenges.models import User
from accounts.serializers import UserSerializer


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('name', 'difficulty', 'languages')
