"""
Notification model and related post hooks
"""
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from accounts.models import User
from challenges.models import SubmissionVote
from social.constants import VALID_NOTIFICATION_TYPES, NOTIFICATION_TYPE_CONTENT_FIELDS
from social.errors import InvalidNotificationType, MissingNotificationContentField, \
    InvalidNotificationContentField
from social.models.managers.notification import NotificationManager


class Notification(models.Model):
    """
    A Notification is a simple notification that a user receives, again facebook-esque
    Since the content here is dynamic (somebody liked your post, new challenge appears in the site, etc),
        we need an HStore field to store data related to the type of the notification.
    """
    recipient = models.ForeignKey(User)
    type = models.CharField(max_length=60)  # no other table for now
    content = JSONField()  # varies depending on the type
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NotificationManager()

    class Meta:
        ordering = ('updated_at', )  # order by updated_at, as we might update notifications to simulate squashing

    @staticmethod
    def is_valid_submission_upvote_notification(submission_vote: SubmissionVote):
        return submission_vote.is_upvote and submission_vote.author != submission_vote.submission.author

    @staticmethod
    def fetch_unread_notifications_for_user(user: User):
        return Notification.objects.filter(recipient=user, is_read=False).order_by('updated_at')

    def is_recipient(self, user: User):
        return self.recipient_id == user.id


from deadline.celery import send_notification


@receiver(pre_save, sender=Notification)
def notification_type_validation(sender, instance, *args, **kwargs):
    # Validate that the type is valid and contains what we expect exactly
    if instance.type not in VALID_NOTIFICATION_TYPES:
        raise InvalidNotificationType(f'{instance.type} is not a valid Notification type!')

    # Assert that each field is present
    required_fields = NOTIFICATION_TYPE_CONTENT_FIELDS[instance.type]
    for field in required_fields:
        if field not in instance.content:
            raise MissingNotificationContentField(
                f'The field {field} must be in the content of Notification of type {instance.type}.')

    # Assert that no other unnecessary fields are present
    if len(required_fields) < len(instance.content.keys()):
        # Some unnecessary field is present
        for field in instance.content.keys():
            if field not in required_fields:
                raise InvalidNotificationContentField(
                    f'The field {field} is not part of the expected content for {instance.type} and is unnecessary!')


@receiver(post_save, sender=Notification)
def notif_post_save_send(sender, instance, created, *args, **kwargs):
    if created:
        send_notification(instance.id)
