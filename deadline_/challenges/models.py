from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from challenges.validators import MaxFloatDigitValidator, PossibleFloatDigitValidator
from accounts.models import User
from sql_queries import (
    SUBMISSION_SELECT_TOP_SUBMISSIONS_FOR_CHALLENGE,
    SUBMISSION_SELECT_LAST_10_SUBMISSIONS_GROUPED_BY_CHALLENGE_BY_AUTHOR,
    SUBMISSION_SELECT_TOP_SUBMISSION_FOR_CHALLENGE_BY_USER)


class Language(models.Model):
    name = models.CharField(unique=True, max_length=30)
    default_code = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Challenge(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.OneToOneField('ChallengeDescription')
    difficulty = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10), PossibleFloatDigitValidator(['0', '5'])])
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    test_file_name = models.CharField(max_length=50)
    test_case_count = models.IntegerField(blank=False)
    category = models.ForeignKey(to='SubCategory', related_name='challenges')
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
    timed_out = models.BooleanField(default=False)  # showing if the majority of the tests have timed out
    elapsed_seconds = models.FloatField(default=0)

    def get_absolute_url(self):
        return '/challenges/{}/submissions/{}'.format(self.challenge_id, self.id)

    def get_votes_count(self):
        """
        Returns the amount of upvote and downvotes this submission has
        :return: (int, int) - (upvote, downvote)
        """
        upvote_count, downvote_count = 0, 0

        for vote in self.votes.all():
            if vote.is_upvote:
                upvote_count += 1
            else:
                downvote_count += 1

        return upvote_count, downvote_count

    @staticmethod
    def fetch_top_submissions_for_challenge(challenge_id):
        """
        Returns the top-rated Submissions for a specific Challenge, one for each User
        """
        return Submission.objects.raw(SUBMISSION_SELECT_TOP_SUBMISSIONS_FOR_CHALLENGE, params=[challenge_id])

    @staticmethod
    def fetch_top_submission_for_challenge_and_user(challenge_id, user_id):
        """
        Returns the top-rated Submission for a specific Challenge from a specific User
        """
        submissions = list(Submission.objects.raw(SUBMISSION_SELECT_TOP_SUBMISSION_FOR_CHALLENGE_BY_USER, params=[challenge_id, user_id]))
        if len(submissions) == 0 or submissions[0].id is None:
            return None
        else:
            return submissions[0]

    @staticmethod
    def fetch_last_10_submissions_for_unique_challenges_by_user(user_id):
        """ Queries the DB for the last 10 submissions issued by the given user, grouped by the challenge """
        return Submission.objects.raw(SUBMISSION_SELECT_LAST_10_SUBMISSIONS_GROUPED_BY_CHALLENGE_BY_AUTHOR,
                                      params=[user_id])


class SubmissionVote(models.Model):
    is_upvote = models.BooleanField()
    submission = models.ForeignKey(to=Submission, related_name='votes')
    author = models.ForeignKey(User)

    class Meta:
        unique_together = ('submission', 'author')


class TestCase(models.Model):
    submission = models.ForeignKey(Submission)
    time = models.FloatField(default=0)
    success = models.BooleanField(default=False)
    pending = models.BooleanField(default=True)
    description = models.CharField(max_length=1000)
    traceback = models.CharField(max_length=2000)
    error_message = models.CharField(max_length=100)
    timed_out = models.BooleanField(default=False)

    class Meta:
        ordering = ['id', ]

    def get_absolute_url(self):
        return '/challenges/{}/submissions/{}/test/{}'.format(
            self.submission.challenge_id, self.submission.id, self.id)


class MainCategory(models.Model):
    """ A Main Category for Challenges. ie: Algorithms """
    name = models.CharField(max_length=100, unique=True)


class SubCategory(models.Model):
    """ A more specific Category for Challenges, ie: Graph Theory """
    name = models.CharField(max_length=100, unique=True)
    meta_category = models.ForeignKey(to=MainCategory, related_name='sub_categories')
    max_score = models.IntegerField(default=0, verbose_name="The maximum score from all the challenges in this subcategory")

    def __str__(self):
        return self.name


class UserSubcategoryProgress(models.Model):
    """ Holds each user's progress in a subcategory """
    user = models.ForeignKey(User)
    subcategory = models.ForeignKey(SubCategory)
    user_score = models.IntegerField(default=0, verbose_name="The score that the user has accumulated for this subcategory")

    class Meta:
        unique_together = ('user', 'subcategory')


class ChallengeDescription(models.Model):
    """ Holds the description for a specific challenge """
    content = models.CharField(max_length=3000)
    input_format = models.CharField(max_length=500)
    output_format = models.CharField(max_length=1000)
    constraints = models.CharField(max_length=1000)
    sample_input = models.CharField(max_length=1000)
    sample_output = models.CharField(max_length=1000)
    explanation = models.CharField(max_length=1000)


class Proficiency(models.Model):
    """
        Constitutes some milestone for a user's progress in a subcategory's challenges
    """
    name = models.CharField(max_length=100, unique=True)
    # represents the needed percentage to achieve this proficiency
    needed_percentage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])


class UserSubcategoryProficiency(models.Model):
    """ Holds each user's proficiency in a given subcategory """
    user = models.ForeignKey(User)
    subcategory = models.ForeignKey(SubCategory)
    proficiency = models.ForeignKey(Proficiency)

    class Meta:
        unique_together = ('user', 'subcategory')
