from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from challenges.validators import MaxFloatDigitValidator, PossibleFloatDigitValidator
from accounts.models import User
from sql_queries import (
    SUBMISSION_SELECT_TOP_SUBMISSIONS_FOR_CHALLENGE,
    SUBMISSION_SELECT_LAST_10_SUBMISSIONS_GROUPED_BY_CHALLENGE_BY_AUTHOR)


class Language(models.Model):
    name = models.CharField(unique=True, max_length=30, primary_key=True)


class Challenge(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.OneToOneField('ChallengeDescription')
    difficulty = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10), PossibleFloatDigitValidator(['0', '5'])])
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    test_file_name = models.CharField(max_length=50)
    test_case_count = models.IntegerField(blank=False)
    category = models.ForeignKey(to='SubCategory', to_field='name', related_name='challenges')
    supported_languages = models.ManyToManyField(Language)

    def get_absolute_url(self):
        return '/challenges/{}'.format(self.id)


class Submission(models.Model):
    challenge = models.ForeignKey(Challenge)
    author = models.ForeignKey(User)
    code = models.CharField(max_length=4000, blank=False)
    task_id = models.CharField(max_length=100, blank=False)
    result_score = models.IntegerField(verbose_name="The points from the challenge", default=0)
    pending = models.BooleanField(default=True)
    compiled = models.BooleanField(default=True)
    compile_error_message = models.CharField(max_length=1000, blank=False)
    language = models.ForeignKey(Language, to_field='name', blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return '/challenges/{}/submissions/{}'.format(self.challenge_id, self.id)

    @staticmethod
    def fetch_top_submissions_for_challenge(challenge_id):
        """
        Returns the top-rated Submissions for a specific Challenge, one for each User
        """
        return Submission.objects.raw(SUBMISSION_SELECT_TOP_SUBMISSIONS_FOR_CHALLENGE, params=[challenge_id])

    @staticmethod
    def fetch_last_10_submissions_for_unique_challenges_by_user(user_id):
        """ Queries the DB for the last 10 submissions issued by the given user, grouped by the challenge """
        return Submission.objects.raw(SUBMISSION_SELECT_LAST_10_SUBMISSIONS_GROUPED_BY_CHALLENGE_BY_AUTHOR,
                                      params=[user_id])


class TestCase(models.Model):
    submission = models.ForeignKey(Submission)
    time = models.CharField(default='0.00s', max_length=5)
    success = models.BooleanField(default=False)
    pending = models.BooleanField(default=True)
    description = models.CharField(max_length=1000)
    traceback = models.CharField(max_length=2000)
    error_message = models.CharField(max_length=100)

    class Meta:
        ordering = ['id', ]

    def get_absolute_url(self):
        return '/challenges/{}/submissions/{}/test/{}'.format(
            self.submission.challenge_id, self.submission.id, self.id)


class MainCategory(models.Model):
    """ A Main Category for Challenges. ie: Algorithms """
    name = models.CharField(max_length=100, unique=True, primary_key=True)


class SubCategory(models.Model):
    """ A more specific Category for Challenges, ie: Graph Theory """
    name = models.CharField(max_length=100, unique=True, primary_key=True)
    meta_category = models.ForeignKey(to=MainCategory, related_name='sub_categories')

    def __str__(self):
        return self.name


class ChallengeDescription(models.Model):
    """ Holds the description for a specific challenge """
    content = models.CharField(max_length=3000)
    input_format = models.CharField(max_length=500)
    output_format = models.CharField(max_length=1000)
    constraints = models.CharField(max_length=1000)
    sample_input = models.CharField(max_length=1000)
    sample_output = models.CharField(max_length=1000)
    explanation = models.CharField(max_length=1000)