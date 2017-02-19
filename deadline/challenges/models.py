from django.db import models


# Create your models here.
class Challenge(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.CharField(max_length=3000)
    rating = models.IntegerField()
    score = models.IntegerField()
    # TODO: Add category once ready

    def get_absolute_url(self):
        return '/challenge/{}'.format(self.id)