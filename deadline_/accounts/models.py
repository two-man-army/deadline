import hashlib, uuid


from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

from accounts.helpers import hash_password


# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class User(AbstractBaseUser):
    USERNAME_FIELD = 'email'
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=30, unique=True)
    password = models.CharField(max_length=30)
    score = models.IntegerField(default=0)
    salt = models.CharField(max_length=40)
    last_submit_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Put in an if, since django calls __init__ twice!
        if not self.salt:
            # Store a random salt and hash the password!
            self.salt = uuid.uuid4().hex
            self.password = hash_password(password=self.password, salt=self.salt)

    def __str__(self):
        return self.username

    def fetch_max_score_for_challenge(self, challenge_id):
        """
        Fetches the maximum score this user has scored for the given challenge
        """
        from challenges.models import Submission

        top_submission = Submission.fetch_top_submission_for_challenge_and_user(challenge_id, self.id)
        max_score = top_submission.maxscore if top_submission else 0
        return max_score
