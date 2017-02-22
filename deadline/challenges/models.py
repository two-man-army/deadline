from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from accounts.models import User


# Create your models here.
class Challenge(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.CharField(max_length=3000)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    score = models.IntegerField(validators=[MinValueValidator(1)])
    test_file_name = models.CharField(max_length=50)
    test_case_count = models.IntegerField(blank=False)
    category = models.ForeignKey(to='SubCategory', to_field='name')

    def get_absolute_url(self):
        return '/challenges/{}'.format(self.id)


class Submission(models.Model):
    challenge = models.ForeignKey(Challenge)
    author = models.ForeignKey(User)
    code = models.CharField(max_length=4000, blank=False)
    task_id = models.CharField(max_length=100, blank=False)
    result_score = models.IntegerField(verbose_name="The points from the challenge", default=0)
    pending = models.BooleanField(default=True)

    def get_absolute_url(self):
        return '/challenges/{}/submissions/{}'.format(self.challenge_id, self.id)


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


class ChallengeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, primary_key=True)


class SubCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, primary_key=True)
    meta_category = models.ForeignKey(to=ChallengeCategory)
