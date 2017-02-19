from django.db import models

from accounts.models import User


# Create your models here.
class Challenge(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.CharField(max_length=3000)
    rating = models.IntegerField()
    score = models.IntegerField()
    # TODO: Add category once ready

    def get_absolute_url(self):
        return '/challenge/{}'.format(self.id)


class Submission(models.Model):
    challenge = models.ForeignKey(Challenge)
    author = models.ForeignKey(User)
    code = models.CharField(max_length=4000, blank=False)

    def get_absolute_url(self):
        return '/submissions/{}'.format(self.id)
