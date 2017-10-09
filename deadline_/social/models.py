from django.contrib.postgres.fields import JSONField
from django.db import models
from django_hstore import hstore
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from accounts.models import User
from challenges.models import SubCategory, UserSubcategoryProficiency, SubmissionComment, ChallengeComment, SubmissionVote
from errors import ForbiddenMethodError
from social.constants import NEWSFEED_ITEM_TYPE_CONTENT_FIELDS, VALID_NEWSFEED_ITEM_TYPES, \
    NW_ITEM_SUBCATEGORY_BADGE_POST, NW_ITEM_SHARE_POST, NW_ITEM_SUBMISSION_LINK_POST, NW_ITEM_CHALLENGE_LINK_POST, \
    NW_ITEM_CHALLENGE_COMPLETION_POST, VALID_NOTIFICATION_TYPES, NOTIFICATION_TYPE_CONTENT_FIELDS, \
    RECEIVE_FOLLOW_NOTIFICATION, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION, RECEIVE_NW_ITEM_LIKE_NOTIFICATION, \
    NEW_CHALLENGE_NOTIFICATION, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION, \
    RECEIVE_SUBMISSION_COMMENT_NOTIFICATION, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION, \
    RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED, \
    RECEIVE_FOLLOW_NOTIFICATION_SQUASHED, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED, \
    RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED, \
    RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED, \
    RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED
from social.errors import InvalidNewsfeedItemType, MissingNewsfeedItemContentField, InvalidNewsfeedItemContentField, \
    LikeAlreadyExistsError, NonExistentLikeError, InvalidNotificationType, MissingNotificationContentField, \
    InvalidNotificationContentField, InvalidFollowError


class NewsfeedItemManager(models.Manager):
    """
    Use a custom NewsfeedItem manager for specific type of NewsfeedItem creation
    """

    def create_subcategory_badge_post(self, user_subcat_prof: UserSubcategoryProficiency):
        """
        Creates a SubcategoryBadgePost

        A SubcategoryBadgePost is a NewsfeedItem which has the following fields as content:
            proficiency_name: - the name of the proficiency (or badge) the user has attained
            subcategory_name: - the name of the subcategory this badge is for
            subcategory_id:   - the id of the subcategory

        ex: Stanislav just earned the Master badge for Graph Algorithms!
        """
        return self.create(author_id=user_subcat_prof.user_id, type=NW_ITEM_SUBCATEGORY_BADGE_POST,
                           content={
                               'proficiency_name': user_subcat_prof.proficiency.name,
                               'subcategory_name': user_subcat_prof.subcategory.name,
                               'subcategory_id': user_subcat_prof.subcategory.id
                           })

    def create_share_post(self, shared_item: 'NewsfeedItem', author: User):
        """
        Creates a 'share' of a NewsfeedItem or in other words, a NewsfeedItem that points to another
        """
        # TODO: Add validation for not creating a share of a share
        return self.create(author_id=author.id, type=NW_ITEM_SHARE_POST, content={'newsfeed_item_id': shared_item.id})

    def create_submission_link(self, submission: 'Submission', author: User):
        """
        Creates a 'link' NewsfeedItem type of a Submission
        """
        return self.create(author_id=author.id, type=NW_ITEM_SUBMISSION_LINK_POST,
                           content={
                               'submission_id': submission.id,
                               'submission_author_id': submission.author.id,
                               'submission_author_name': submission.author.username,
                               'submission_code_snippet': submission.code[:200],  # for now up until 200 characters, we'll see how this works
                               'submission_language_name': submission.language.name,
                               'submission_language_loc': 0  # temporary, as we do not store this anywhere
                           })

    def create_challenge_link(self, challenge: 'Challenge', author: User):
        """
        Creates a 'link' NewsfeedItem type of a Submission
        """
        return self.create(author_id=author.id, type=NW_ITEM_CHALLENGE_LINK_POST,
                           content={
                               'challenge_id': challenge.id,
                               'challenge_name': challenge.name,
                               'challenge_subcategory_name': challenge.category.name,
                               'challenge_difficulty': challenge.difficulty
                           })

    def create_challenge_completion_post(self, submission: 'Submission'):
        """
        Creates a NewsfeedItem of type ChallengeCompletion
            ex: Stanislav has completed challenge Firefox with 100/100 score after 30 attempts
        """
        challenge = submission.challenge
        author: User = submission.author
        if not submission.has_solved_challenge():
            raise Exception(f'Submission has not solved the challenge!')

        return self.create(author_id=author.id, type=NW_ITEM_CHALLENGE_COMPLETION_POST,
                           content={
                               'challenge_id': challenge.id,
                               'challenge_name': challenge.name,
                               'submission_id': submission.id,
                               'challenge_score': challenge.score,
                               'attempts_count': author.fetch_unsuccessful_challenge_attempts_count(challenge)
                           })


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


# TODO: Move these Notifications to another place
# TODO: Figure out what a CommentReply notification should look like, as currently
# TODO:     some hold the content of the replier's comment and some hold the content of the original comment
class NotificationManager(hstore.HStoreManager):
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

    def create_receive_submission_upvote_notification(self, submission: 'Submission', liker: User):
        """
        Creates a Notification that a User has liked your submission
        ex: Stanislav has liked your Submission for Challenge Robert's Pass
        """
        return ReceiveSubmissionUpvoteNotificationManager(self, submission=submission, liker=liker).create()

    def create_receive_nw_item_like_notification(self, nw_item: NewsfeedItem, liker: User):
        return ReceiveNWItemLikeNotificationManager(self, nw_item=nw_item, liker=liker).create()

    def create_new_challenge_notification(self, recipient: User, challenge: 'Challenge'):
        """ A notification which notifies the user that a new challenge has appeared on the site"""
        # TODO: Figure out a way to add new challenges and create notifications.

        return self._create(recipient=recipient, type=NEW_CHALLENGE_NOTIFICATION,
                            content={'challenge_name': challenge.name, 'challenge_id': challenge.id,
                                     'challenge_subcategory_name': challenge.category.name})

    def create_nw_item_comment_notification(self, nw_item: NewsfeedItem, commenter: User):
        """ A notification which notifies the user that somebody has commented on his NewsfeedItem """
        return ReceiveNWItemCommentNotificationManager(self, nw_item=nw_item, commenter=commenter).create()

    def create_nw_item_comment_reply_notification(self, nw_comment: NewsfeedItemComment, reply: NewsfeedItemComment):
        return ReceiveNWItemCommentReplyNotificationManager(self, nw_comment=nw_comment, reply=reply).create()

    def create_submission_comment_notification(self, comment: SubmissionComment):
        return ReceiveSubmissionCommentNotificationManager(self, comment=comment).create()

    def create_submission_comment_reply_notification(self, comment: SubmissionComment):
        return ReceiveSubmissionCommentReplyNotificationManager(self, reply=comment).create()

    def create_challenge_comment_reply_notification(self, reply: ChallengeComment):
        return ReceiveChallengeCommentReplyNotificationManager(self, reply=reply).create()


class SquashableNotificationManagerBase:
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

    def add_to_squashed_type(self):
        """ Defines Notification-specific logic for adding the current notification's data into the squashed one """
        raise NotImplementedError()

    def get_normal_content(self) -> dict:
        """
        Returns the content of the single non-squashed notification.
        This is meant to be overriden for each specific Notification
        """
        raise NotImplementedError()

    def create_new_squashed_content(self) -> dict:
        """
        Combines the old notification's content with the new one being created
        """
        raise NotImplementedError()

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

    def __init__(self, notification_manager: NotificationManager, nw_item: NewsfeedItem, liker: User):
        super().__init__(notification_manager)
        self.recipient = nw_item.author
        self.liker = liker
        self.nw_item = nw_item

    def get_normal_content(self):
        # TODO: Change nw_item_content, nw_item_type to nw_content, nw_type or vice-versa. but be consistent!
        return {'nw_content': self.nw_item.content, 'nw_type': self.nw_item.type,
                'nw_item_id': self.nw_item.id,
                'liker_id': self.liker.id, 'liker_name': self.liker.username}

    def create_new_squashed_content(self):
        return {
            'nw_content': self.nw_item.content,
            'nw_type': self.nw_item.type,
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

    def __init__(self, notification_manager: NotificationManager, nw_item: NewsfeedItem, commenter: User):
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

    def __init__(self, notification_manager: NotificationManager, nw_comment: NewsfeedItemComment,
                 reply: NewsfeedItemComment):
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
