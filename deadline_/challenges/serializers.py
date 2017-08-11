from collections import OrderedDict

from rest_framework import serializers
from challenges.models import Challenge, Submission, TestCase, MainCategory, SubCategory, ChallengeDescription, Language, UserSubcategoryProficiency
from challenges.models import User


class ChallengeDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeDescription
        exclude = ('id', )


class ChallengeSerializer(serializers.ModelSerializer):
    description = ChallengeDescriptionSerializer()
    category = serializers.StringRelatedField()
    supported_languages = serializers.StringRelatedField(many=True)

    class Meta:
        model = Challenge
        fields = ('id', 'name', 'difficulty', 'score', 'description', 'test_case_count', 'category',
                  'supported_languages')


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
    category = serializers.StringRelatedField()
    user_max_score = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ('id', 'name', 'difficulty', 'score', 'category', 'user_max_score')

    def get_user_max_score(self, obj):
        # TODO: get User from __init__, not request
        user = getattr(self.context.get('request', None), 'user', None)
        if user is None:
            return 0
        else:
            return user.fetch_max_score_for_challenge(challenge_id=obj.id)


class SubmissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    challenge = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.StringRelatedField(read_only=True)
    result_score = serializers.IntegerField(read_only=True)
    pending = serializers.BooleanField(read_only=True)
    language = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ('id', 'challenge', 'author', 'code', 'result_score', 'pending', 'created_at',
                  'compiled', 'compile_error_message', 'language', 'timed_out', 'upvote_count', 'downvote_count')

    def get_language(self, obj):
        return obj.language.name

    def get_upvote_count(self, obj):
        upvote_count, _ = obj.get_votes_count()
        return upvote_count

    def get_downvote_count(self, obj):
        _, downvote_count = obj.get_votes_count()
        return downvote_count

    def to_representation(self, instance: Submission):
        """
        Modification to add four variables to the serialized data
            - user_has_voted - Boolean indicating if the user has voted at all for this
            - user_has_upvoted - Boolean indicating if the user has upvoted the submission (user_has_voted must be true)
            - upvote_count - int showing the amount of upvotes this submission has
            - downvote_count - int showing the amount of downvotes this submission has
        """
        from accounts.models import User
        result = super().to_representation(instance)
        user: User = getattr(self.context.get('request', None), 'user', None)
        # TODO: Make user be passed in __init__
        if user is None:
            result['user_has_voted'] = False
            result['user_has_upvoted'] = False
        else:
            user_vote = user.get_vote_for_submission(submission_id=instance.id)
            if user_vote is None:
                result['user_has_voted'] = False
                result['user_has_upvoted'] = False
            else:
                result['user_has_voted'] = True
                result['user_has_upvoted'] = user_vote.is_upvote

        return result


class LimitedSubmissionSerializer(serializers.ModelSerializer):
    """ Serializes everything about a submission except its code """
    id = serializers.IntegerField(read_only=True)
    challenge = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.StringRelatedField(read_only=True)
    result_score = serializers.IntegerField(read_only=True)
    pending = serializers.BooleanField(read_only=True)
    language = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ('id', 'challenge', 'author', 'result_score', 'pending', 'created_at',
                  'compiled', 'compile_error_message', 'language', 'timed_out')

    def get_language(self, obj):
        return obj.language.name

    def to_representation(self, instance: Submission):
        """
        Modification to add four variables to the serialized data
            - user_has_voted - Boolean indicating if the user has voted at all for this
            - user_has_upvoted - Boolean indicating if the user has upvoted the submission (user_has_voted must be true)
            - upvote_count - int showing the amount of upvotes this submission has
            - downvote_count - int showing the amount of downvotes this submission has
        """
        from accounts.models import User
        result = super().to_representation(instance)
        user:User = getattr(self.context.get('request', None), 'user', None)
        # TODO: Move to helper
        # TODO: Make user be passed in __init__
        if user is None:
            result['user_has_voted'] = False
            result['user_has_upvoted'] = False
        else:
            user_vote = user.get_vote_for_submission(submission_id=instance.id)
            if user_vote is None:
                result['user_has_voted'] = False
                result['user_has_upvoted'] = False
            else:
                result['user_has_voted'] = True
                result['user_has_upvoted'] = user_vote.is_upvote

        upvote_count, downvote_count = instance.get_votes_count()
        result['upvote_count'] = upvote_count
        result['downvote_count'] = downvote_count

        return result


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
        fields = ('submission', 'pending', 'success', 'time', 'description', 'traceback', 'error_message', 'timed_out')


class MainCategorySerializer(serializers.ModelSerializer):
    sub_categories = serializers.StringRelatedField(many=True)

    class Meta:
        model = MainCategory
        fields = ('name', 'sub_categories')


class SubCategorySerializer(serializers.ModelSerializer):
    challenges = LimitedChallengeSerializer(many=True)
    proficiency = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = ('name', 'challenges', 'max_score', 'proficiency')

    def get_proficiency(self, obj):
        # attach the current user's proficiency
        user: User = getattr(self.context.get('request', None), 'user', None)
        user_proficiency: UserSubcategoryProficiency = user.fetch_subcategory_proficiency(subcategory_id=obj.id)
        proficiency_object = OrderedDict()
        proficiency_object['name'] = user_proficiency.proficiency.name
        proficiency_object['user_score'] = user_proficiency.user_score

        return proficiency_object
