"""
Models related to a NewsfeedItem
"""

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from accounts.models import User
from social.constants import NEWSFEED_ITEM_TYPE_CONTENT_FIELDS, VALID_NEWSFEED_ITEM_TYPES
from social.errors import InvalidNewsfeedItemType, MissingNewsfeedItemContentField, InvalidNewsfeedItemContentField, \
    LikeAlreadyExistsError, NonExistentLikeError
from social.models.managers.newsfeed_item import NewsfeedItemManager
from social.models.notification import Notification


class NewsfeedItem(models.Model):
    """
    NewsfeedItem is a model that holds a single item in the facebook-esque NewsFeed (or Activity Feed)
        of the website.
    Since the content here is dynamic (you can share a submission, display you've complete a challenge, etc),
        we need an HStore field to store data related to the type of the post.
    e.g
    {
        type: "completed_challenge"
        content: {
            "challenge_id": 1,
            "submission_id": 1
        }
    },
    {
        type: "created_course"
        content: {
            "course_id": 1
        }
    }
    """
    author = models.ForeignKey(User)
    type = models.CharField(max_length=30)  # no other table for now
    content = JSONField()  # varies depending on the type
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NewsfeedItemManager()

    def get_absolute_url(self):
        return f'/social/feed/items/{self.id}'

    def like(self, user: User, create_notif=True):
        if NewsfeedItemLike.objects.filter(newsfeed_item=self, author=user).exists():
            raise LikeAlreadyExistsError(f'The Like from User {user.id} for Item {self.id} does already exists!')

        nw_like = NewsfeedItemLike.objects.create(author=user, newsfeed_item=self)

        if create_notif and user != self.author:
            Notification.objects.create_receive_nw_item_like_notification(nw_item=self, liker=user)

        return nw_like

    def remove_like(self, user: User):
        like = NewsfeedItemLike.objects.filter(newsfeed_item=self, author=user).first()
        if like is None:
            raise NonExistentLikeError(f'The Like from User {user.id} for Item {self.id} does not exist!')

        like.delete()

    def add_comment(self, author: User, content: str, to_notify: bool=True):
        if to_notify and self.author != author:
            Notification.objects.create_nw_item_comment_notification(commenter=author, nw_item=self)
        return NewsfeedItemComment.objects.create(author=author, content=content, newsfeed_item=self)


@receiver(pre_save, sender=NewsfeedItem)
def nw_item_validation(sender, instance, *args, **kwargs):
    # Validate that the type is valid and contains what we expect exactly
    if instance.type not in VALID_NEWSFEED_ITEM_TYPES:
        raise InvalidNewsfeedItemType(f'{instance.type} is not a valid NewsfeedItem type!')

    # Assert that each field is present
    required_fields = NEWSFEED_ITEM_TYPE_CONTENT_FIELDS[instance.type]
    for field in required_fields:
        if field not in instance.content:
            raise MissingNewsfeedItemContentField(
                f'The field {field} must be in the content of NewsfeedItem of type {instance.type}.')

    # Assert that no other unnecessary fields are present
    if len(required_fields) < len(instance.content.keys()):
        # Some unnecessary field is present
        for field in instance.content.keys():
            if field not in required_fields:
                raise InvalidNewsfeedItemContentField(
                    f'The field {field} is not part of the expected content for {instance.type} and is unnecessary!')


class NewsfeedItemComment(models.Model):
    newsfeed_item = models.ForeignKey(NewsfeedItem, related_name='comments')
    author = models.ForeignKey(User)
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, related_name='replies', default=None)

    def add_reply(self, author, content, to_notify=True):
        reply = NewsfeedItemComment.objects.create(newsfeed_item=self.newsfeed_item, parent=self, author=author, content=content)
        if to_notify and author != self.author:
            Notification.objects.create_nw_item_comment_reply_notification(nw_comment=self, reply=reply)
        return reply


class NewsfeedItemLike(models.Model):
    newsfeed_item = models.ForeignKey(NewsfeedItem, related_name='likes')
    author = models.ForeignKey(User)
    unique_together = ('newsfeed_item', 'author')
