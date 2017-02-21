from rest_framework import serializers
from challenges.models import Challenge, Submission, TestCase


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ('name', 'rating', 'score', 'description', 'test_case_count')


class SubmissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    challenge = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Submission
        fields = ('id', 'challenge', 'author', 'code')


class TestCaseSerializer(serializers.ModelSerializer):
    submission = serializers.PrimaryKeyRelatedField(read_only=True)
    success = serializers.BooleanField(read_only=True)
    pending = serializers.BooleanField(read_only=True)
    time = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    traceback = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True)

    class Meta:
        model = TestCase
        fields = ('submission', 'pending', 'success', 'time', 'description', 'traceback', 'error_message')
