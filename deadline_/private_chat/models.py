from datetime import timedelta, datetime
from uuid import uuid4

import jwt
from django.db import models
from django.conf import settings
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import date as dj_date
from django.utils.translation import ugettext as _
from model_utils.models import TimeStampedModel, SoftDeletableModel

from accounts.models import User
from private_chat.helpers import generate_dialog_tokens


class DialogManager(models.Manager):
    def get_or_create_dialog_with_users(self, user_owner, user_opponent):
        """
        Gets or creates the dialog between user_owner and user_opponent
        """
        if not self.filter(Q(owner=user_owner, opponent=user_opponent) | Q(opponent=user_owner, owner=user_opponent)).exists():
            return self.create(owner=user_owner, opponent=user_opponent)

        return self.filter(Q(owner=user_owner, opponent=user_opponent) | Q(opponent=user_owner, owner=user_opponent)).first()


class Dialog(models.Model):
    """
    Dialogs have two tokens, once for each participant.
    Said participant needs to prove its him with this token and said token should expire frequently
    """
    owner = models.ForeignKey(User, verbose_name=_("Dialog owner"), related_name="selfDialogs")
    owner_token = models.CharField(max_length=200, null=True)
    opponent = models.ForeignKey(User, verbose_name=_("Dialog opponent"))
    opponent_token = models.CharField(max_length=200, null=True)
    secret_key = models.CharField(max_length=50, null=True)
    objects = DialogManager()

    def __str__(self):
        return f'Chat between {self.owner.username} and {self.opponent.username}'

    def tokens_are_expired(self) -> bool:
        """ Checks whether the current tokens are expired """
        try:
            jwt.decode(self.owner_token, self.secret_key)
            jwt.decode(self.opponent_token, self.secret_key)
            return False
        except jwt.ExpiredSignatureError:
            return True

    def refresh_tokens(self, force=False):
        if not force and self.tokens_are_expired():
            raise Exception("Will not reset Dialog's tokens when they are not expired without being forced!")
        secret_key, owner_token, opponent_token = generate_dialog_tokens(self.owner.username, self.opponent.username)
        self.secret_key = secret_key
        self.owner_token = owner_token
        self.opponent_token = opponent_token
        self.save()

    def token_is_valid(self, token):
        return token in [self.owner_token, self.opponent_token] and not self.tokens_are_expired()


@receiver(post_save, sender=Dialog)
def populate_tokens(sender, instance, created, *args, **kwargs):
    """
        Create tokens
    """
    if not created:
        return
    secret_key, owner_token, opponent_token = generate_dialog_tokens(instance.owner.username, instance.opponent.username)
    instance.secret_key = secret_key
    instance.owner_token = owner_token
    instance.opponent_token = opponent_token
    instance.save()


class Message(TimeStampedModel, SoftDeletableModel):
    dialog = models.ForeignKey(Dialog, verbose_name=_("Dialog"), related_name="messages")
    sender = models.ForeignKey(User, verbose_name=_("Author"), related_name="messages")
    text = models.TextField(verbose_name=_("Message text"))
    all_objects = models.Manager()

    def get_formatted_create_datetime(self):
        return dj_date(self.created, settings.DATETIME_FORMAT)

    def __str__(self):
        return self.sender.username + "(" + self.get_formatted_create_datetime() + ") - '" + self.text + "'"
