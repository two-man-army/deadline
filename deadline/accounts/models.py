import hashlib, uuid


from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver

from rest_framework.authtoken.models import Token


# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class User(AbstractBaseUser):
    USERNAME_FIELD = 'email'
    username = models.CharField(max_length=30)
    email = models.EmailField(max_length=30, unique=True)
    password = models.CharField(max_length=30)
    score = models.IntegerField(default=0)
    salt = models.CharField(max_length=40)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store a random salt and hash the password!
        self.salt = uuid.uuid4().hex
        self.password = hashlib.sha512((self.password + self.salt).encode('utf-8')).hexdigest()
