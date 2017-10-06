from unittest.mock import patch, MagicMock

from django.test import TestCase
from radar import random_datetime

from deadline.settings import RABBITMQ_CLIENT  # MagicMock under testing
from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import UserFactory, SubmissionFactory, ChallengeFactory, SubmissionCommentFactory, \
    ChallengeCommentFactory
from errors import ForbiddenMethodError
from social.constants import RECEIVE_FOLLOW_NOTIFICATION, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION, \
    RECEIVE_NW_ITEM_LIKE_NOTIFICATION, NEW_CHALLENGE_NOTIFICATION, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION, \
    RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION, \
    RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION, \
    RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED
from social.errors import InvalidNotificationType, MissingNotificationContentField, InvalidNotificationContentField, \
    InvalidFollowError
from social.models import Notification, NewsfeedItem, NewsfeedItemComment
from social.serializers import NotificationSerializer


class NotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_objects_create_raises_error(self):
        with self.assertRaises(ForbiddenMethodError):
            Notification.objects.create(recipient=self.auth_user, type=RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION,
                                        content={'content': 'Hello I like turtles'})

    def test_model_save_raises_if_invalid_notification_type(self):
        """ An error should be raised if we enter an invalid newsfeeditem type """
        with self.assertRaises(InvalidNotificationType):
            Notification.objects._create(recipient=self.auth_user, type='TANK',
                                         content={'content': 'Hello I like turtles'})

    @patch('social.models.VALID_NOTIFICATION_TYPES', ['test_type'])
    @patch('social.models.NOTIFICATION_TYPE_CONTENT_FIELDS', {'test_type': ['1', '2']})
    def test_model_save_raises_if_missing_newsfeed_content_field(self):
        """ Given a valid Newsfeed Type, an error should be raised if a required field is missing """
        with self.assertRaises(MissingNotificationContentField):
            Notification.objects._create(recipient=self.auth_user, type='test_type',
                                         content={})

    @patch('social.models.VALID_NOTIFICATION_TYPES', ['test_type'])
    @patch('social.models.NOTIFICATION_TYPE_CONTENT_FIELDS', {'test_type': ['1', '2']})
    def test_model_save_raises_if_invalid_newsfeed_content_field(self):
        """ Given a valid Newsfeed Type, an error should be raised if an invalid field is added,
                regardless if all the right ones are supplied (memory is expensive) """
        with self.assertRaises(InvalidNotificationContentField):
            Notification.objects._create(recipient=self.auth_user, type='test_type',
                                         content={'1': 'Hello I like turtles', '2': 'pf', 'tank': 'yo'})

    @patch('social.models.send_notification')
    def test_post_save_notif_sends_create_message_to_rabbit_mq(self, mock_send_notif):
        sec_user = UserFactory()
        notif = Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=sec_user)

        # Assert it is called only on creation
        notif.follower = self.auth_user
        notif.save()

        mock_send_notif.assert_called_once_with(notif.id)

    def test_create_new_challenge_notification(self):
        chal = ChallengeFactory()
        expected_content = {
            'challenge_name': chal.name,
            'challenge_id': chal.id,
            'challenge_subcategory_name': chal.category.name
        }
        notif = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=chal)

        self.assertEqual(notif.type, NEW_CHALLENGE_NOTIFICATION)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(expected_content, notif.content)

    def test_is_recipient_returns_true(self):
        notif = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=ChallengeFactory())
        self.assertTrue(notif.is_recipient(self.auth_user))

    def test_is_recipient_returns_false_when_not_recipient(self):
        notif = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=ChallengeFactory())
        self.assertFalse(notif.is_recipient(MagicMock(id=111)))


class ReceiveFollowNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_create_receive_follow_notification(self):
        sec_user = UserFactory()
        notif = Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=sec_user)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notif.type, RECEIVE_FOLLOW_NOTIFICATION)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(notif.content, {'follower_id': sec_user.id, 'follower_name': sec_user.username})

    def test_create_receive_follow_notification_raises_invalid_follow_if_same_follower(self):
        with self.assertRaises(InvalidFollowError):
            Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=self.auth_user)

    def test_create_multiple_notifications_should_be_squashed(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        expected_content = {
            'followers': [
                {'follower_id': sec_user.id, 'follower_name': sec_user.username},
                {'follower_id': third_user.id, 'follower_name': third_user.username},
                {'follower_id': fourth_user.id, 'follower_name': fourth_user.username}
            ]
        }
        for user in [sec_user, third_user, fourth_user]:
            notif = Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=user)
            if user != sec_user:
                self.assertEqual(notif.type, RECEIVE_FOLLOW_NOTIFICATION_SQUASHED)
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_FOLLOW_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_multiple_notifications_should_not_be_squashed_if_read(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        for user in [sec_user, third_user, fourth_user]:
            expected_content = {'follower_id': user.id, 'follower_name': user.username}

            notif = Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=user)

            self.assertEqual(notif.type, RECEIVE_FOLLOW_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(Notification.objects.count(), 3)


class ReceiveSubmissionUpvoteNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_create_receive_submission_upvote_notification(self):
        sec_user = UserFactory()
        submission = SubmissionFactory(author=self.auth_user)
        notif = Notification.objects.create_receive_submission_upvote_notification(submission=submission, liker=sec_user)
        expected_content = {
            'submission_id': submission.id,
            'challenge_id': submission.challenge.id,
            'challenge_name': submission.challenge.name,
            'liker_id': sec_user.id,
            'liker_name': sec_user.username
        }
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(expected_content, notif.content)

    def test_create_receive_submission_upvote_notification_doesnt_create_if_same_user(self):
        submission = SubmissionFactory(author=self.auth_user)
        notif = Notification.objects.create_receive_submission_upvote_notification(submission=submission, liker=self.auth_user)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_multiple_notifications_should_be_squashed_into_one(self):
        """ If three users upvote without the notif being read, notifs should be squashed """
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        submission = SubmissionFactory(author=self.auth_user)
        expected_content = {
            'submission_id': submission.id,
            'challenge_id': submission.challenge.id,
            'challenge_name': submission.challenge.name,
            'likers': [
                {
                    'liker_id': sec_user.id,
                    'liker_name': sec_user.username
                },
                {
                    'liker_id': third_user.id,
                    'liker_name': third_user.username
                },
                {
                    'liker_id': fourth_user.id,
                    'liker_name': fourth_user.username
                },
            ]
        }
        for user in [sec_user, third_user, fourth_user]:
            notif = Notification.objects.create_receive_submission_upvote_notification(submission=submission,
                                                                                       liker=user)
            if user != sec_user:
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(expected_content, notif.content)
        # TODO: Except Squashable

    def test_multiple_notifications_should_not_be_squashed_if_read(self):
        """ If three users upvote but the person reads each notif one by one, notif should NOT be squashed """
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()

        submission = SubmissionFactory(author=self.auth_user)
        for user in [sec_user, third_user, fourth_user]:
            expected_content = {
                'submission_id': submission.id,
                'challenge_id': submission.challenge.id,
                'challenge_name': submission.challenge.name,
                'liker_id': user.id,
                'liker_name': user.username
            }
            notif = Notification.objects.create_receive_submission_upvote_notification(submission=submission,
                                                                                       liker=user)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION)
            self.assertEqual(notif.recipient, self.auth_user)
            self.assertEqual(expected_content, notif.content)
        self.assertEqual(Notification.objects.count(), 3)


class ReceiveNWItemLikeNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_create_receive_nw_item_like_notification(self):
        sec_user = UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = {'nw_content': nw_item.content,
                            'nw_type': nw_item.type, 'liker_id': sec_user.id, 'liker_name': sec_user.username}

        notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=nw_item, liker=sec_user)

        self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION)
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_receive_nw_item_like_notification_doesnt_create_if_liker_is_recipient(self):
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=nw_item, liker=self.auth_user)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_be_squashed(self):
        second_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        sample_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = {
            'nw_content': sample_nw_item.content,
            'nw_type': sample_nw_item.type,
            'likers': [
                {'liker_id': second_user.id, 'liker_name': second_user.username},
                {'liker_id': third_user.id, 'liker_name': third_user.username},
                {'liker_id': fourth_user.id, 'liker_name': fourth_user.username}
            ]
        }

        for user in [second_user, third_user, fourth_user]:
            notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=sample_nw_item, liker=user)
            if user != second_user:
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(notif.content, expected_content)

    def test_create_multiple_notifications_should_not_be_squashed_if_read(self):
        second_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        sample_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        for user in [second_user, third_user, fourth_user]:
            notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=sample_nw_item, liker=user)
            notif.is_read = True
            notif.save()
            expected_content = {
                'nw_content': sample_nw_item.content, 'nw_type': sample_nw_item.type,
                'liker_id': user.id, 'liker_name': user.username
            }
            self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION)
            self.assertEqual(notif.recipient, self.auth_user)
            self.assertEqual(notif.content, expected_content)

        self.assertEqual(Notification.objects.count(), 3)


class ReceiveNWItemCommentNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_create_nw_item_comment_notification(self):
        sec_user = UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = {
            'commenter_name': sec_user.username, 'commenter_id': sec_user.id,
            'nw_item_content': nw_item.content,
            'nw_item_id': nw_item.id, 'nw_item_type': nw_item.type
        }
        notif = Notification.objects.create_nw_item_comment_notification(nw_item=nw_item, commenter=sec_user)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first(), notif)
        self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION)
        self.assertEqual(notif.recipient, nw_item.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_nw_item_comment_notification_doesnt_create_if_commenter_is_recipient(self):
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        notif = Notification.objects.create_nw_item_comment_notification(nw_item=nw_item, commenter=self.auth_user)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_be_squashed(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = {
            'nw_item_content': nw_item.content,
            'nw_item_id': nw_item.id, 'nw_item_type': nw_item.type,
            'commenters': [
                {'commenter_name': sec_user.username, 'commenter_id': sec_user.id},
                {'commenter_name': third_user.username, 'commenter_id': third_user.id},
                {'commenter_name': fourth_user.username, 'commenter_id': fourth_user.id},
            ]
        }

        for user in [sec_user, third_user, fourth_user]:
            notif = Notification.objects.create_nw_item_comment_notification(nw_item=nw_item, commenter=user)
            if user != sec_user:
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED)
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_multiple_notifications_should_not_be_squashed_if_read(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        for user in [sec_user, third_user, fourth_user]:
            expected_content = {
                'nw_item_content': nw_item.content,
                'nw_item_id': nw_item.id, 'nw_item_type': nw_item.type,
                'commenter_name': user.username, 'commenter_id': user.id,
            }
            notif = Notification.objects.create_nw_item_comment_notification(nw_item=nw_item, commenter=user)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)

        self.assertEqual(Notification.objects.count(), 3)


class ReceiveChallengeCommentReplyNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.setup_proficiencies()
        self.chal = ChallengeFactory()
        self.chal_comment = ChallengeCommentFactory(challenge=self.chal, author=self.auth_user)

    def test_create_notification_comment_reply_notif(self):
        chal_reply = ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment)
        expected_content = {
            'challenge_id': self.chal.id,
            'challenge_name': self.chal.name,
            'comment_id': chal_reply.id,
            'comment_content': chal_reply.content,
            'commenter_id': chal_reply.author.id,
            'commenter_name': chal_reply.author.username
        }

        notif = Notification.objects.create_challenge_comment_reply_notification(reply=chal_reply)

        self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION)
        self.assertEqual(notif.recipient, self.chal_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_notification_comment_reply_notif_not_created_if_commenter_replies_to_himself(self):
        chal_reply = ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment, author=self.auth_user)

        notif = Notification.objects.create_challenge_comment_reply_notification(reply=chal_reply)

        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_get_squashed(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment, author=us)
                   for us in [sec_user, third_user, fourth_user]]
        expected_content = {
            'challenge_id': self.chal.id,
            'challenge_name': self.chal.name,
            'commenters': [
                {'commenter_id': sec_user.id, 'commenter_name': sec_user.username},
                {'commenter_id': third_user.id, 'commenter_name': third_user.username},
                {'commenter_id': fourth_user.id, 'commenter_name': fourth_user.username},
            ]
        }

        for reply in replies:
            notif = Notification.objects.create_challenge_comment_reply_notification(reply=reply)
            if reply != replies[0]:
                self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.chal_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_multiple_notifications_should_not_get_squashed_if_read(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment, author=us)
                   for us in [sec_user, third_user, fourth_user]]

        for reply in replies:
            expected_content = {
                'challenge_id': self.chal.id,
                'challenge_name': self.chal.name,
                'comment_id': reply.id,
                'comment_content': reply.content,
                'commenter_id': reply.author.id,
                'commenter_name': reply.author.username
            }
            notif = Notification.objects.create_challenge_comment_reply_notification(reply=reply)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION)
            self.assertEqual(notif.recipient, self.chal_comment.author)
            self.assertEqual(notif.content, expected_content)

        self.assertEqual(Notification.objects.count(), 3)


class ReceiveNWItemCommentReplyNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_create_nw_item_comment_reply_notif(self):
        sec_user = UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                                   to_notify=False)
        reply = NewsfeedItemComment.objects.create(newsfeed_item=nw_item,
                                                   parent=nw_comment, author=sec_user,
                                                   content='secured')
        expected_content = {
            'nw_comment_id': nw_comment.id, 'commenter_id': reply.author.id,
            'commenter_name': reply.author.username, 'comment_content': reply.content
        }

        notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=nw_comment, reply=reply)

        self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION)
        self.assertEqual(notif.recipient, nw_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_nw_item_comment_reply_notif_doesnt_create_if_recipient_is_replier(self):
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                                   to_notify=False)
        reply = NewsfeedItemComment.objects.create(newsfeed_item=nw_item,
                                                   parent=nw_comment, author=self.auth_user,
                                                   content='secured')

        notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=nw_comment, reply=reply)

        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_be_squashed(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                              to_notify=False)
        replies = [NewsfeedItemComment.objects.create(newsfeed_item=nw_item, parent=nw_comment,
                                                      author=us, content='secured')
                   for us in [sec_user, third_user, fourth_user]]

        expected_content = {
            'nw_comment_id': nw_comment.id,
            'commenters': [{'commenter_id': reply.author.id, 'commenter_name': reply.author.username }
                           for reply in replies]
        }
        for reply in replies:
            notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=nw_comment, reply=reply)
            if reply != replies[0]:
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_multiple_notifications_should_not_be_squashed_if_read(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                              to_notify=False)
        replies = [NewsfeedItemComment.objects.create(newsfeed_item=nw_item, parent=nw_comment,
                                                      author=us, content='secured')
                   for us in [sec_user, third_user, fourth_user]]

        for reply in replies:
            notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=nw_comment, reply=reply)
            expected_content = {
                'nw_comment_id': nw_comment.id, 'commenter_id': reply.author.id,
                'commenter_name': reply.author.username, 'comment_content': reply.content
            }
            notif.is_read = True
            notif.save()
            self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)

        self.assertEqual(Notification.objects.count(), 3)


class ReceiveSubmissionCommentNotification(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.setup_proficiencies()
        self.subm = SubmissionFactory(author_id=self.auth_user.id)

    def test_create_submission_comment_notification(self):
        subm_comment = SubmissionCommentFactory(submission=self.subm)
        expected_content = {
            'submission_id': self.subm.id, 'challenge_id': self.subm.challenge.id,
            'challenge_name': self.subm.challenge.name,
            'commenter_name': subm_comment.author.username, 'comment_content': subm_comment.content,
            'comment_id': subm_comment.id, 'commenter_id': subm_comment.author.id,
        }

        notif = Notification.objects.create_submission_comment_notification(comment=subm_comment)
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)
        self.assertEqual(notif.recipient, self.subm.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_submission_comment_notification_not_created_if_author_comments_himself(self):
        subm_comment = SubmissionCommentFactory(submission=self.subm, author=self.auth_user)
        notif = Notification.objects.create_submission_comment_notification(comment=subm_comment)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_be_squashed(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        comments = [self.subm.add_comment(us, 'x', to_notify=False) for us in [sec_user, third_user, fourth_user]]
        expected_content = {
            'submission_id': self.subm.id, 'challenge_id': self.subm.challenge.id,
            'challenge_name': self.subm.challenge.name,
            'commenters': [
                {'commenter_name': subm_comment.author.username, 'commenter_id': subm_comment.author.id}
                for subm_comment in comments
            ]
        }

        for comment in comments:
            notif = Notification.objects.create_submission_comment_notification(comment=comment)
            if comment != comments[0]:
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(notif.content, expected_content)

    def test_create_multiple_notifications_should_not_be_squashed_if_read(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        comments = [self.subm.add_comment(us, 'x', to_notify=False) for us in [sec_user, third_user, fourth_user]]

        for comment in comments:
            expected_content = {
                'submission_id': self.subm.id, 'challenge_id': self.subm.challenge.id,
                'challenge_name': self.subm.challenge.name,
                'commenter_name': comment.author.username, 'comment_content': comment.content,
                'comment_id': comment.id, 'commenter_id': comment.author.id,
            }
            notif = Notification.objects.create_submission_comment_notification(comment=comment)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)
            self.assertEqual(notif.recipient, self.auth_user)
            self.assertEqual(notif.content, expected_content)

        self.assertEqual(Notification.objects.count(), 3)


class ReceiveSubmissionCommentReplyNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.setup_proficiencies()
        self.subm = SubmissionFactory(author_id=self.auth_user.id)
        self.subm_comment = SubmissionCommentFactory(submission=self.subm, author=self.auth_user)

    def test_create_submission_comment_reply_notif(self):
        sec_user = UserFactory()
        subm_reply = SubmissionCommentFactory(submission=self.subm, author=sec_user, parent=self.subm_comment)
        expected_content = {
            'submission_id': subm_reply.submission.id, 'challenge_id': subm_reply.submission.challenge.id,
            'challenge_name': subm_reply.submission.challenge.name, 'comment_id': subm_reply.id,
            'comment_content': subm_reply.content, 'commenter_id': subm_reply.author.id,
            'commenter_name': subm_reply.author.username
        }

        notif = Notification.objects.create_submission_comment_reply_notification(comment=subm_reply)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notif, Notification.objects.first())
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION)
        self.assertEqual(notif.recipient, self.subm_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_submission_comment_reply_notif_not_created_if_commenter_replies_to_himself(self):
        subm_reply = SubmissionCommentFactory(submission=self.subm, author=self.auth_user, parent=self.subm_comment)

        notif = Notification.objects.create_submission_comment_reply_notification(comment=subm_reply)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_get_squashed(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [SubmissionCommentFactory(submission=self.subm, author=us, parent=self.subm_comment)
                   for us in [sec_user, third_user, fourth_user]]
        expected_content = {
            'submission_id': self.subm.id, 'challenge_id': self.subm.challenge.id,
            'challenge_name': self.subm.challenge.name,
            'commenters': [
                {
                    'commenter_id': reply.author.id,
                    'commenter_name': reply.author.username
                } for reply in replies
            ]
        }
        for reply in replies:
            notif = Notification.objects.create_submission_comment_reply_notification(comment=reply)
            if reply != replies[0]:
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_multiple_notifications_should_not_get_squashed_if_read(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [SubmissionCommentFactory(submission=self.subm, author=us, parent=self.subm_comment)
                   for us in [sec_user, third_user, fourth_user]]

        for reply in replies:
            notif = Notification.objects.create_submission_comment_reply_notification(comment=reply)
            expected_content = {
                'submission_id': reply.submission.id, 'challenge_id': reply.submission.challenge.id,
                'challenge_name': reply.submission.challenge.name, 'comment_id': reply.id,
                'comment_content': reply.content, 'commenter_id': reply.author.id,
                'commenter_name': reply.author.username
            }

            self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(Notification.objects.count(), 3)


# TODO: !!!!
# TODO: Test two consecutive notifications for different submissions do not overwrite each other!
# TODO: !!!!


class NotificationHelperMethodTests(TestCase, TestHelperMixin):
    """
    Tests the methods on the Notification class
    """
    def setUp(self):
        self.create_user_and_auth_token()

    def test_is_valid_submission_upvote_notification(self):
        """
        A SubmissionUpvote notification should be done when the vote is a upvote and the author is not the submission's author!
        """
        submission_vote_mock = MagicMock(is_upvote=True, author=1, submission=MagicMock(author=2))

        self.assertTrue(Notification.is_valid_submission_upvote_notification(submission_vote_mock))

    def test_is_valid_submission_upvote_notification_isnt_valid_if_not_upvote(self):
        """
        A SubmissionUpvote notification should be done when the vote is a upvote and the author is not the submission's author!
        """
        submission_vote_mock = MagicMock(is_upvote=False, author=1, submission=MagicMock(author=2))

        self.assertFalse(Notification.is_valid_submission_upvote_notification(submission_vote_mock))

    def test_is_valid_submission_upvote_notification_isnt_valid_if_voter_is_submission_author(self):
        """
        A SubmissionUpvote notification should be done when the vote is a upvote and the author is not the submission's author!
        """
        submission_vote_mock = MagicMock(is_upvote=True, author=1, submission=MagicMock(author=1))

        self.assertFalse(Notification.is_valid_submission_upvote_notification(submission_vote_mock))

    def test_fetch_unread_notifications_for_user(self):
        sec_user = UserFactory()
        chal = ChallengeFactory()
        notifs = [Notification.objects.create_new_challenge_notification(recipient=(self.auth_user if i % 2 == 0 else sec_user),
                                                                         challenge=chal) for i in range(20)]
        for i, notif in enumerate(notifs):
            notif.updated_at = random_datetime()
            notif.is_read = True if i % 2 == 0 else False
            notif.save()

        # notifs should be ordered by updated_at
        expected_notifs = list(sorted([notif for notif in notifs if notif.recipient == self.auth_user and not notif.is_read],
                                      key=lambda x: x.updated_at))
        self.assertEqual(list(Notification.fetch_unread_notifications_for_user(self.auth_user)), expected_notifs)


class NotificationSerializerTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_serialize(self):
        chal = ChallengeFactory()
        expected_notif_content = {
            'challenge_name': chal.name,
            'challenge_id': chal.id,
            'challenge_subcategory_name': chal.category.name
        }

        notif = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=chal)
        expected_data = {
            'id': notif.id,
            'type': notif.type,
            'updated_at': notif.updated_at.isoformat().replace('+00:00', 'Z'),
            'content': expected_notif_content
        }

        self.assertEqual(notif.content, expected_notif_content)
        self.assertEqual(expected_data, NotificationSerializer(notif).data)

    def test_multiple_serializations_orders_by_updated_at(self):
        chal = ChallengeFactory()
        notifs = [Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=chal) for _ in range(15)]
        for notif in notifs:
            notif.updated_at = random_datetime()
            notif.save()

        expected_data = NotificationSerializer(list(sorted(notifs, key=lambda x: x.updated_at)), many=True).data
        self.assertEqual(expected_data, NotificationSerializer(notifs, many=True).data)
