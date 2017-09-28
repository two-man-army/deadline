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
    RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION
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

    def test_create_receive_follow_notification(self):
        sec_user = UserFactory()
        notif = Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=sec_user)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notif.type, RECEIVE_FOLLOW_NOTIFICATION)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(notif.content, {'follower_id': sec_user.id, 'follower_name': sec_user.username})

    @patch('social.models.send_notification')
    def test_post_save_notif_sends_create_message_to_rabbit_mq(self, mock_send_notif):
        sec_user = UserFactory()
        notif = Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=sec_user)

        # Assert it is called only on creation
        notif.type = 'tank'
        notif.save()

        mock_send_notif.assert_called_once_with(notif.id)

    def test_create_receive_follow_notification_raises_invalid_follow_if_same_follower(self):
        with self.assertRaises(InvalidFollowError):
            Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=self.auth_user)

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

    def test_create_nw_item_comment_notification(self):
        sec_user = UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = {'commenter_name': sec_user.username, 'commenter_id': sec_user.id,
                            'nw_item_content': nw_item.content, 'nw_item_id': nw_item.id, 'nw_item_type': nw_item.type}
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

    def test_create_submission_comment_notification(self):
        self.setup_proficiencies()
        subm = SubmissionFactory(author_id=self.auth_user.id)
        subm_comment = SubmissionCommentFactory(submission=subm)
        expected_content = {
            'submission_id': subm.id, 'challenge_id': subm.challenge.id, 'challenge_name': subm.challenge.name,
            'commenter_name': subm_comment.author.username, 'comment_content': subm_comment.content,
            'comment_id': subm_comment.id, 'commenter_id': subm_comment.author.id,
        }

        notif = Notification.objects.create_submission_comment_notification(comment=subm_comment)
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)
        self.assertEqual(notif.recipient, subm.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_submission_comment_notification_not_created_if_author_comments_himself(self):
        self.setup_proficiencies()
        subm = SubmissionFactory(author_id=self.auth_user.id)
        subm_comment = SubmissionCommentFactory(submission=subm, author=self.auth_user)
        notif = Notification.objects.create_submission_comment_notification(comment=subm_comment)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_submission_comment_reply_notif(self):
        self.setup_proficiencies()
        sec_user = UserFactory()
        subm = SubmissionFactory(author_id=self.auth_user.id)
        subm_comment = SubmissionCommentFactory(submission=subm, author=self.auth_user)
        subm_reply = SubmissionCommentFactory(submission=subm, author=sec_user, parent=subm_comment)
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
        self.assertEqual(notif.recipient, subm_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_submission_comment_reply_notif_not_created_if_commenter_replies_to_himself(self):
        self.setup_proficiencies()
        subm = SubmissionFactory(author_id=self.auth_user.id)
        subm_comment = SubmissionCommentFactory(submission=subm, author=self.auth_user)
        subm_reply = SubmissionCommentFactory(submission=subm, author=self.auth_user, parent=subm_comment)

        notif = Notification.objects.create_submission_comment_reply_notification(comment=subm_reply)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_notification_comment_reply_notif(self):
        self.setup_proficiencies()
        chal = ChallengeFactory()
        chal_comment = ChallengeCommentFactory(challenge=chal, author=self.auth_user)
        chal_reply = ChallengeCommentFactory(challenge=chal, parent=chal_comment)
        expected_content = {
            'challenge_id': chal.id,
            'challenge_name': chal.name,
            'comment_id': chal_reply.id,
            'comment_content': chal_reply.content,
            'commenter_id': chal_reply.author.id,
            'commenter_name': chal_reply.author.username
        }

        notif = Notification.objects.create_challenge_comment_reply_notification(reply=chal_reply)

        self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION)
        self.assertEqual(notif.recipient, chal_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_notification_comment_reply_notif_not_created_if_commenter_replies_to_himself(self):
        self.setup_proficiencies()
        chal = ChallengeFactory()
        chal_comment = ChallengeCommentFactory(challenge=chal, author=self.auth_user)
        chal_reply = ChallengeCommentFactory(challenge=chal, parent=chal_comment, author=self.auth_user)

        notif = Notification.objects.create_challenge_comment_reply_notification(reply=chal_reply)

        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_is_recipient_returns_true(self):
        notif = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=ChallengeFactory())
        self.assertTrue(notif.is_recipient(self.auth_user))

    def test_is_recipient_returns_false_when_not_recipient(self):
        notif = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=ChallengeFactory())
        self.assertFalse(notif.is_recipient(MagicMock(id=111)))


class NotificationHelperMethodTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

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
