from rest_framework import serializers
from challenges.models import Challenge, Submission, TestCase, MainCategory, SubCategory, ChallengeDescription, Language


class ChallengeDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeDescription
        exclude = ('id', )


class ChallengeSerializer(serializers.ModelSerializer):
    description = ChallengeDescriptionSerializer()

    class Meta:
        model = Challenge
        fields = ('id', 'name', 'difficulty', 'score', 'description', 'test_case_count', 'category', 'supported_languages')


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class LimitedChallengeSerializer(serializers.ModelSerializer):
    """
    Returns the main information about a Challenge
        and the current user's max score (this requires the challenge object to have user_max_score attached to it).
    Used, for example, when listing challenges.
    """

    class Meta:
        model = Challenge
        fields = ('id', 'name', 'difficulty', 'score', 'category')  # user_max_score is added as well but more implicitly

    def to_representation(self, instance):
        """
        Modification to add the user_max_score to the serialized data
        """
        result = super().to_representation(instance)

        user = getattr(self.context.get('request', None), 'user', None)
        if user is None:
            result['user_max_score'] = 0
        else:
            result['user_max_score'] = user.fetch_max_score_for_challenge(challenge_id=instance.id)

        return result


class SubmissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    challenge = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.StringRelatedField(read_only=True)
    result_score = serializers.IntegerField(read_only=True)
    pending = serializers.BooleanField(read_only=True)

    class Meta:
        model = Submission
        fields = ('id', 'challenge', 'author', 'code', 'result_score', 'pending', 'created_at',
                  'compiled', 'compile_error_message', 'language')


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


class MainCategorySerializer(serializers.ModelSerializer):
    sub_categories = serializers.StringRelatedField(many=True)

    class Meta:
        model = MainCategory
        fields = ('name', 'sub_categories')


class SubCategorySerializer(serializers.ModelSerializer):
    challenges = LimitedChallengeSerializer(many=True)

    class Meta:
        model = SubCategory
        fields = ('name', 'challenges')
