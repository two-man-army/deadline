"""
Defines the NotificationManager for the Notification model
and all the helper managers, which manage specific Notification creation and squashing
"""
from abc import ABC, abstractmethod

from django_hstore.hstore import HStoreManager

from accounts.models import User
from challenges.models import SubmissionComment, ChallengeComment, Submission, Challenge
from errors import ForbiddenMethodError
from social.constants import (
    RECEIVE_FOLLOW_NOTIFICATION, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION, RECEIVE_NW_ITEM_LIKE_NOTIFICATION,
    NEW_CHALLENGE_NOTIFICATION, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION,
    RECEIVE_SUBMISSION_COMMENT_NOTIFICATION, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION,
    RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED,
    RECEIVE_FOLLOW_NOTIFICATION_SQUASHED, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED,
    RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED,
    RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED,
    RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED
)
from social.errors import InvalidFollowError

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from social.models.newsfeed_item import NewsfeedItem, NewsfeedItemComment


class NotificationManager(HStoreManager):
    """
    Use a custom Notification manager for specific type of Notification creation
    """
    def create(self, *args, **kwargs):
        raise ForbiddenMethodError('This method is not intended to be used. '
                                   'Please use any of the create_xxx methods to create a specific type of notification')

    def _create(self, *args, **kwargs):
        """
        The create() method, intentionally marked as private as it is not intended for usage at all,
            except for testing purposes
        """
        return super().create(*args, **kwargs)

    def create_receive_follow_notification(self, recipient: User, follower: User):
        """
        Creates a Notification that a User has been followed
        ex: Stanislav has followed you!
        """
        return ReceiveFollowNotificationManager(self, recipient=recipient, follower=follower).create()

    def create_receive_submission_upvote_notification(self, submission: Submission, liker: User):
        """
        Creates a Notification that a User has liked your submission
        ex: Stanislav has liked your Submission for Challenge Robert's Pass
        """
        return ReceiveSubmissionUpvoteNotificationManager(self, submission=submission, liker=liker).create()

    def create_receive_nw_item_like_notification(self, nw_item: 'NewsfeedItem', liker: User):
        return ReceiveNWItemLikeNotificationManager(self, nw_item=nw_item, liker=liker).create()

    def create_new_challenge_notification(self, recipient: User, challenge: Challenge):
        """ A notification which notifies the user that a new challenge has appeared on the site"""
        # TODO: Figure out a way to add new challenges and create notifications.

        return self._create(recipient=recipient, type=NEW_CHALLENGE_NOTIFICATION,
                            content={'challenge_name': challenge.name, 'challenge_id': challenge.id,
                                     'challenge_subcategory_name': challenge.category.name})

    def create_nw_item_comment_notification(self, nw_item: 'NewsfeedItem', commenter: User):
        """ A notification which notifies the user that somebody has commented on his NewsfeedItem """
        return ReceiveNWItemCommentNotificationManager(self, nw_item=nw_item, commenter=commenter).create()

    def create_nw_item_comment_reply_notification(self, nw_comment: 'NewsfeedItemComment', reply: 'NewsfeedItemComment'):
        return ReceiveNWItemCommentReplyNotificationManager(self, nw_comment=nw_comment, reply=reply).create()

    def create_submission_comment_notification(self, comment: SubmissionComment):
        return ReceiveSubmissionCommentNotificationManager(self, comment=comment).create()

    def create_submission_comment_reply_notification(self, comment: SubmissionComment):
        return ReceiveSubmissionCommentReplyNotificationManager(self, reply=comment).create()

    def create_challenge_comment_reply_notification(self, reply: ChallengeComment):
        return ReceiveChallengeCommentReplyNotificationManager(self, reply=reply).create()


class SquashableNotificationManagerBase(ABC):
    """
    This is a wrapper to a NotificationManager for creating a notification of a specific type.
    Needed variable definitions:
        self.recipient - User object which is meant to receive this Notification
    """
    def __init__(self, notification_manager: NotificationManager):
        self._check_types()
        self.notification_manager: NotificationManager = notification_manager

    def create(self):
        """
        Creates the notification, first running a check if we should create it at all and
            then delegating to the appropriate method
        """
        if self.should_skip_creation():
            return

        if self.should_squash():
            return self.squash()
        else:
            return self.notification_manager._create(recipient=self.recipient, type=self.TYPE,
                                                     content=self.get_normal_content())

    def should_squash(self) -> bool:
        """
        Finds and saves a squashable notification.
        The way it determines if this notification should be squashed is -
            it simply checks if another notification is eligible to be squashed with the one being creates.
        Here you can define further logic, like checking that the latest notification is not too old
        """
        self.last_notification = self.find_last_squashable_notification()
        return self.last_notification is not None

    def squash(self) -> 'Notification':
        """ Squashes the notification we're about to create with another one """
        if self.last_notification.type == self.TYPE:
            notification = self.convert_to_squashed_type()
        else:
            notification = self.merge_into_squashed_notification()

        return notification

    def convert_to_squashed_type(self) -> 'Notification':
        """
        Converts the latest squashable notification into a SQUASHED type
            and combines it with the one being created
        """
        self.last_notification.type = self.SQUASHED_TYPE
        self.last_notification.content = self.create_new_squashed_content()
        self.last_notification.save()
        return self.last_notification

    def merge_into_squashed_notification(self) -> 'Notification':
        """ Merges the current notification into the latest_notification and returns it """
        self.add_to_squashed_type()
        self.last_notification.save()
        return self.last_notification

    def find_last_squashable_notification(self) -> 'Notification':
        """
        This method should get the last Notification that is not read and is the same as our type
        """
        content_filter = self.get_last_notification_content_filter()
        last_notification_query = self.notification_manager.filter(
            type__in=[self.TYPE, self.SQUASHED_TYPE],
            is_read=False,
            recipient=self.recipient)

        if content_filter:
            last_notification_query = last_notification_query.filter(content__contains=content_filter)

        return last_notification_query.last()

    def should_skip_creation(self) -> bool:
        """
        Either raises an exception or returns a boolean indicating if we should skip the creation
        """
        return bool(self.create_check())

    @abstractmethod
    def add_to_squashed_type(self):
        """ Defines Notification-specific logic for adding the current notification's data into the squashed one """
        pass

    @abstractmethod
    def get_normal_content(self) -> dict:
        """
        Returns the content of the single non-squashed notification.
        This is meant to be overriden for each specific Notification
        """
        pass

    @abstractmethod
    def create_new_squashed_content(self) -> dict:
        """
        Combines the old notification's content with the new one being created
        """
        pass

    def get_last_notification_content_filter(self) -> dict:
        """ Returns the `content` we want our last squashable notification to have. """
        return {}

    def create_check(self) -> bool:
        """
        Runs a check we'd like to have prior to creation.
        """
        pass

    def _check_types(self):
        requires_attrs = ['TYPE', 'SQUASHED_TYPE']
        for req_attr in requires_attrs:
            if not hasattr(self.__class__, req_attr):
                raise Exception(f'A static {req_attr} variable must be defined!')


class ReceiveFollowNotificationManager(SquashableNotificationManagerBase):
    """
    Raises InvalidFollowError
    """
    TYPE = RECEIVE_FOLLOW_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_FOLLOW_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, recipient: User, follower: User):
        super().__init__(notification_manager)
        self.recipient = recipient
        self.follower = follower

    def get_normal_content(self):
        return {
            'follower_id': self.follower.id,
            'follower_name': self.follower.username
        }

    def create_new_squashed_content(self) -> dict:
        """
        Combines the old notification's content with the new one being created
        """
        return {
            'followers': [
                self.last_notification.content,
                {'follower_id': self.follower.id, 'follower_name': self.follower.username}
            ]
        }

    def add_to_squashed_type(self):
        new_entry = {'follower_id': self.follower.id, 'follower_name': self.follower.username}
        self.last_notification.content['followers'].append(new_entry)

    def create_check(self) -> bool:
        """
        Runs a check we'd like to have prior to creation.
        """
        if self.follower == self.recipient:
            raise InvalidFollowError('You cannot follow yourself!')


class ReceiveSubmissionUpvoteNotificationManager(SquashableNotificationManagerBase):
    TYPE = RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, submission: 'Submission', liker: User):
        super().__init__(notification_manager)
        self.recipient = submission.author
        self.submission = submission
        self.liker = liker

    def get_normal_content(self):
        return {
            'submission_id': self.submission.id,
            'challenge_id': self.submission.challenge.id,
            'challenge_name': self.submission.challenge.name,
            'liker_id': self.liker.id,
            'liker_name': self.liker.username
        }

    def create_new_squashed_content(self) -> dict:
        return {
            'submission_id': self.submission.id,
            'challenge_id': self.submission.challenge.id,
            'challenge_name': self.submission.challenge.name,
            'likers': [
                {
                    'liker_id': self.last_notification.content['liker_id'],
                    'liker_name': self.last_notification.content['liker_name']
                },
                {'liker_id': self.liker.id, 'liker_name': self.liker.username}
            ]
        }

    def add_to_squashed_type(self):
        new_entry = {'liker_id': self.liker.id, 'liker_name': self.liker.username}
        self.last_notification.content['likers'].append(new_entry)

    def get_last_notification_content_filter(self) -> dict:
        return {'submission_id': self.submission.id}

    def create_check(self) -> bool:
        if self.liker == self.submission.author:
            return True


class ReceiveNWItemLikeNotificationManager(SquashableNotificationManagerBase):
    """
    A notification that a user has liked your NewsfeedItem
    """
    TYPE = RECEIVE_NW_ITEM_LIKE_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, nw_item: 'NewsfeedItem', liker: User):
        super().__init__(notification_manager)
        self.recipient = nw_item.author
        self.liker = liker
        self.nw_item = nw_item

    def get_normal_content(self):
        return {'nw_item_content': self.nw_item.content, 'nw_item_type': self.nw_item.type,
                'nw_item_id': self.nw_item.id,
                'liker_id': self.liker.id, 'liker_name': self.liker.username}

    def create_new_squashed_content(self):
        return {
            'nw_item_content': self.nw_item.content,
            'nw_item_type': self.nw_item.type,
            'nw_item_id': self.nw_item.id,
            'likers': [
                {'liker_id': self.last_notification.content['liker_id'], 'liker_name': self.last_notification.content['liker_name']},
                {'liker_id': self.liker.id, 'liker_name': self.liker.username}
            ]
        }

    def add_to_squashed_type(self):
        self.last_notification.content['likers'].append({'liker_id': self.liker.id, 'liker_name': self.liker.username})

    def get_last_notification_content_filter(self) -> dict:
        return {'nw_item_id': self.nw_item.id}

    def create_check(self) -> bool:
        if self.liker == self.nw_item.author:
            return True


class ReceiveNWItemCommentNotificationManager(SquashableNotificationManagerBase):
    """
    A notification that a user has liked your NewsfeedItem
    """
    TYPE = RECEIVE_NW_ITEM_COMMENT_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, nw_item: 'NewsfeedItem', commenter: User):
        super().__init__(notification_manager)
        self.recipient = nw_item.author
        self.commenter = commenter
        self.nw_item = nw_item

    def get_normal_content(self) -> dict:
        return {
            'nw_item_content': self.nw_item.content,
            'nw_item_type': self.nw_item.type, 'nw_item_id': self.nw_item.id,
            'commenter_id': self.commenter.id, 'commenter_name': self.commenter.username
        }

    def create_new_squashed_content(self) -> dict:
        return {
            'nw_item_content': self.nw_item.content,
            'nw_item_type': self.nw_item.type,
            'nw_item_id': self.nw_item.id,
            'commenters': [
                {'commenter_id': self.last_notification.content['commenter_id'], 'commenter_name': self.last_notification.content['commenter_name']},
                {'commenter_id': self.commenter.id, 'commenter_name': self.commenter.username}
            ]
        }

    def add_to_squashed_type(self):
        self.last_notification.content['commenters'].append({'commenter_id': self.commenter.id, 'commenter_name': self.commenter.username})

    def get_last_notification_content_filter(self) -> dict:
        return {'nw_item_id': self.nw_item.id}

    def create_check(self):
        if self.commenter == self.nw_item.author:
            return True


class ReceiveNWItemCommentReplyNotificationManager(SquashableNotificationManagerBase):
    """
    A notification that a user has replied on your comment (on a NewsfeedItem)
    """
    TYPE = RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, nw_comment: 'NewsfeedItemComment',
                 reply: 'NewsfeedItemComment'):
        super().__init__(notification_manager)
        self.reply = reply
        self.comment = nw_comment
        self.nw_item = nw_comment.newsfeed_item
        self.recipient = nw_comment.author

    def get_normal_content(self) -> dict:
        return {
            'nw_comment_id': self.comment.id,
            'replier_id': self.reply.author.id,
            'replier_name': self.reply.author.username,
            'reply_content': self.reply.content
        }

    def create_new_squashed_content(self) -> dict:
        return {
            'nw_comment_id': self.comment.id,
            'repliers': [
                {
                    'replier_id': self.last_notification.content['replier_id'],
                    'replier_name': self.last_notification.content['replier_name']
                },
                {'replier_id': self.reply.author.id, 'replier_name': self.reply.author.username}
            ]
        }

    def add_to_squashed_type(self):
        self.last_notification.content['repliers'].append({'replier_id': self.reply.author.id,
                                                           'replier_name': self.reply.author.username})

    def get_last_notification_content_filter(self) -> dict:
        return {'nw_comment_id': self.comment.id}

    def create_check(self) -> bool:
        if self.comment.author == self.reply.author:
            return True


class ReceiveSubmissionCommentNotificationManager(SquashableNotificationManagerBase):
    """
    A notification that a user has replied on your comment (on a NewsfeedItem)
    """
    TYPE = RECEIVE_SUBMISSION_COMMENT_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, comment: SubmissionComment):
        super().__init__(notification_manager)
        self.comment: SubmissionComment = comment
        self.submission = comment.submission
        self.recipient = self.submission.author

    def get_normal_content(self) -> dict:
        return {
            'submission_id': self.submission.id,
            'challenge_id': self.submission.challenge.id,
            'challenge_name': self.submission.challenge.name,
            'commenter_name': self.comment.author.username,
            'commenter_id': self.comment.author.id,
            'comment_content': self.comment.content,
            'comment_id': self.comment.id
        }

    def create_new_squashed_content(self) -> dict:
        return {
            'submission_id': self.submission.id, 'challenge_id': self.submission.challenge.id,
            'challenge_name': self.submission.challenge.name,
            'commenters': [
                {
                    'commenter_id': self.last_notification.content['commenter_id'],
                    'commenter_name': self.last_notification.content['commenter_name']
                },
                {'commenter_id': self.comment.author.id, 'commenter_name': self.comment.author.username}
            ]
        }

    def add_to_squashed_type(self):
        self.last_notification.content['commenters'].append({'commenter_id': self.comment.author.id,
                                                             'commenter_name': self.comment.author.username})

    def get_last_notification_content_filter(self) -> dict:
        return {'submission_id': self.submission.id}

    def create_check(self) -> bool:
        if self.comment.author == self.submission.author:
            return True


class ReceiveChallengeCommentReplyNotificationManager(SquashableNotificationManagerBase):
    """
    A notification that a user has liked your NewsfeedItem
    """
    TYPE = RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, reply: ChallengeComment):
        super().__init__(notification_manager)
        self.reply = reply
        self.comment = reply.parent
        self.challenge = reply.challenge
        self.recipient = self.comment.author

    def get_normal_content(self) -> dict:
        return {
            'challenge_id': self.challenge.id,
            'challenge_name': self.challenge.name,
            'comment_id': self.comment.id,
            'reply_id': self.reply.id,
            'reply_content': self.reply.content,
            'replier_id': self.reply.author.id,
            'replier_name': self.reply.author.username
        }

    def create_new_squashed_content(self) -> dict:
        return {
            'challenge_id': self.challenge.id,
            'challenge_name': self.challenge.name,
            'comment_id': self.comment.id,
            'repliers': [
                {'replier_id': self.last_notification.content['replier_id'], 'replier_name': self.last_notification.content['replier_name']},
                {'replier_id': self.reply.author.id, 'replier_name': self.reply.author.username}
            ]
        }

    def add_to_squashed_type(self):
        self.last_notification.content['repliers'].append({'replier_id': self.reply.author.id,
                                                           'replier_name': self.reply.author.username})

    def get_last_notification_content_filter(self) -> dict:
        return {'challenge_id': self.challenge.id, 'comment_id': self.comment.id}

    def create_check(self) -> bool:
        if self.comment.author == self.reply.author:
            return True


class ReceiveSubmissionCommentReplyNotificationManager(SquashableNotificationManagerBase):
    """
    A notification that a user has liked your NewsfeedItem
    """
    TYPE = RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION
    SQUASHED_TYPE = RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED

    def __init__(self, notification_manager: NotificationManager, reply: SubmissionComment):
        super().__init__(notification_manager)
        self.reply: SubmissionComment = reply
        self.comment = reply.parent
        self.submission = self.comment.submission
        self.recipient = self.comment.author

    def get_normal_content(self) -> dict:
        return {
            'submission_id': self.submission.id,
            'challenge_id': self.submission.challenge.id,
            'challenge_name': self.submission.challenge.name,
            'comment_id': self.comment.id,
            'replier_name': self.reply.author.username,
            'replier_id': self.reply.author.id,
            'reply_content': self.reply.content,
            'reply_id': self.reply.id
        }

    def create_new_squashed_content(self) -> dict:
        return {
            'submission_id': self.submission.id,
            'challenge_id': self.submission.challenge.id,
            'challenge_name': self.submission.challenge.name,
            'comment_id': self.comment.id,
            'repliers': [
                {'replier_id': self.last_notification.content['replier_id'], 'replier_name': self.last_notification.content['replier_name']},
                {'replier_id': self.reply.author.id, 'replier_name': self.reply.author.username}
            ]
        }

    def add_to_squashed_type(self):
        self.last_notification.content['repliers'].append({'replier_id': self.reply.author.id,
                                                           'replier_name': self.reply.author.username})

    def get_last_notification_content_filter(self) -> dict:
        return {'comment_id': self.comment.id}

    def create_check(self) -> bool:
        if self.reply.author == self.submission.author:
            return True
