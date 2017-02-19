from rest_framework import serializers
from challenges.models import Challenge, Submission


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ('name', 'rating', 'score', 'description')


class SubmissionSerializer(serializers.ModelSerializer):
    challenge = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Submission
        fields = ('challenge', 'author', 'code')
