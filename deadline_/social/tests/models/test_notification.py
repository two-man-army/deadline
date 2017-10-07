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
    RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED, RECEIVE_FOLLOW_NOTIFICATION_SQUASHED, \
    RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED, \
    RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED
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

    def test_create_multiple_notifications_should_get_squashed_into_one(self):
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

    def test_create_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        for user in [sec_user, third_user, fourth_user]:
            expected_content = {'follower_id': user.id, 'follower_name': user.username}

            notif = Notification.objects.create_receive_follow_notification(recipient=self.auth_user, follower=user)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_FOLLOW_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(Notification.objects.count(), 3)


class ReceiveSubmissionUpvoteNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def build_content(self, submission, liker):
        return {
            'submission_id': submission.id,
            'challenge_id': submission.challenge.id,
            'challenge_name': submission.challenge.name,
            'liker_id': liker.id,
            'liker_name': liker.username
        }

    def build_squashed_content(self, submission, likers):
        return {
            'submission_id': submission.id,
            'challenge_id': submission.challenge.id,
            'challenge_name': submission.challenge.name,
            'likers': [
                {
                    'liker_id': us.id,
                    'liker_name': us.username
                } for us in likers
            ]
        }

    def test_create_receive_submission_upvote_notification(self):
        sec_user = UserFactory()
        submission = SubmissionFactory(author=self.auth_user)
        expected_content = self.build_content(submission, sec_user)

        notif = Notification.objects.create_receive_submission_upvote_notification(submission=submission, liker=sec_user)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(expected_content, notif.content)

    def test_create_receive_submission_upvote_notification_doesnt_create_if_same_user(self):
        submission = SubmissionFactory(author=self.auth_user)
        notif = Notification.objects.create_receive_submission_upvote_notification(submission=submission, liker=self.auth_user)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_multiple_notifications_should_get_squashed_into_one(self):
        """ If three users upvote without the notif being read, notifs should be squashed """
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        submission = SubmissionFactory(author=self.auth_user)
        expected_content = self.build_squashed_content(submission, [sec_user, third_user, fourth_user])

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

    def test_multiple_notifications_different_submissions_should_get_squashed_separately(self):
        sec_user, third_user, fourth_user, fifth_user = UserFactory(), UserFactory(), UserFactory(), UserFactory()
        first_submission = SubmissionFactory(author=self.auth_user)
        second_submission = SubmissionFactory(author=self.auth_user)

        for user, subm_to_vote in [(sec_user, first_submission), (third_user, second_submission),
                                   (fourth_user, first_submission), (fifth_user, second_submission)]:
            notif = Notification.objects.create_receive_submission_upvote_notification(submission=subm_to_vote,
                                                                                       liker=user)
            if user in [sec_user, third_user]:
                # there are the first voters, so nothing to be squashed with
                self.assertEqual(notif.content, self.build_content(subm_to_vote, user))
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION)
            else:
                if user == fourth_user:
                    users = [sec_user, fourth_user]
                elif user == fifth_user:
                    users = [third_user, fifth_user]
                self.assertEqual(notif.content, self.build_squashed_content(subm_to_vote, users))
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION_SQUASHED).count(), 2)

    def test_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        """ If three users upvote but the person reads each notif one by one, notif should NOT be squashed """
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()

        submission = SubmissionFactory(author=self.auth_user)
        for user in [sec_user, third_user, fourth_user]:
            expected_content = self.build_content(submission, user)
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

    def build_content(self, nw_item, liker):
        return {
            'nw_content': nw_item.content,
            'nw_type': nw_item.type,
            'nw_item_id': nw_item.id,
            'liker_id': liker.id,
            'liker_name': liker.username
        }

    def build_squashed_content(self, nw_item, likers):
        return {
            'nw_content': nw_item.content,
            'nw_type': nw_item.type,
            'nw_item_id': nw_item.id,
            'likers': [
                {'liker_id': us.id, 'liker_name': us.username}
                for us in likers
            ]
        }

    def test_create_receive_nw_item_like_notification(self):
        sec_user = UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = self.build_content(nw_item, sec_user)

        notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=nw_item, liker=sec_user)

        self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION)
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_receive_nw_item_like_notification_doesnt_create_if_liker_is_recipient(self):
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=nw_item, liker=self.auth_user)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_get_squashed_into_one(self):
        second_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        sample_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = self.build_squashed_content(sample_nw_item, [second_user, third_user, fourth_user])

        for user in [second_user, third_user, fourth_user]:
            notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=sample_nw_item, liker=user)
            if user != second_user:
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(notif.content, expected_content)

    def test_two_notifications_different_nw_item_should_not_get_squashed(self):
        second_user, third_user = UserFactory(), UserFactory()
        sample_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        second_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        first_notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=sample_nw_item, liker=second_user)
        second_notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=second_nw_item, liker=third_user)

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_NW_ITEM_LIKE_NOTIFICATION).count(), 2)
        first_notif.refresh_from_db()
        self.assertEqual(first_notif.content, self.build_content(sample_nw_item, second_user))
        self.assertEqual(second_notif.content, self.build_content(second_nw_item, third_user))

    def test_multiple_notifications_different_nw_item_should_get_squashed_separately(self):
        """ Obviously, two likes for different nw_items should not get squashed together"""
        second_user, third_user, fourth_user, fifth_user = UserFactory(), UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        second_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        for us, item_to_vote in [(second_user, nw_item), (third_user, second_nw_item),
                                 (fourth_user, nw_item), (fifth_user, second_nw_item)]:
            notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=item_to_vote, liker=us)
            if us in [second_user, third_user]:
                # first voters
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION)
                self.assertEqual(notif.content, self.build_content(item_to_vote, us))
            else:
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION_SQUASHED)
                if us == fourth_user:
                    likers = [second_user, fourth_user]
                else:
                    likers = [third_user, fifth_user]
                self.assertEqual(notif.content, self.build_squashed_content(item_to_vote, likers))
        self.assertEqual(Notification.objects.count(), 2)

    def test_create_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        second_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        sample_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        for user in [second_user, third_user, fourth_user]:
            expected_content = self.build_content(sample_nw_item, user)

            notif = Notification.objects.create_receive_nw_item_like_notification(nw_item=sample_nw_item, liker=user)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_NW_ITEM_LIKE_NOTIFICATION)
            self.assertEqual(notif.recipient, self.auth_user)
            self.assertEqual(notif.content, expected_content)

        self.assertEqual(Notification.objects.count(), 3)


class ReceiveNWItemCommentNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def build_content(self, nw_item, commenter):
        return {
            'commenter_name': commenter.username, 'commenter_id':commenter.id,
            'nw_item_content': nw_item.content,
            'nw_item_id': nw_item.id, 'nw_item_type': nw_item.type
        }

    def build_squashed_content(self, nw_item, commenters):
        return {
            'nw_item_content': nw_item.content,
            'nw_item_id': nw_item.id, 'nw_item_type': nw_item.type,
            'commenters': [
                {'commenter_name': us.username, 'commenter_id': us.id}
                for us in commenters
            ]
        }

    def test_create_nw_item_comment_notification(self):
        sec_user = UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = self.build_content(nw_item, sec_user)
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

    def test_create_multiple_notifications_should_get_squashed_into_one(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        expected_content = self.build_squashed_content(nw_item, [sec_user, third_user, fourth_user])

        for user in [sec_user, third_user, fourth_user]:
            notif = Notification.objects.create_nw_item_comment_notification(nw_item=nw_item, commenter=user)
            if user != sec_user:
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED)
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        for user in [sec_user, third_user, fourth_user]:
            expected_content = self.build_content(nw_item, user)

            notif = Notification.objects.create_nw_item_comment_notification(nw_item=nw_item, commenter=user)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)

        self.assertEqual(Notification.objects.count(), 3)

    def test_two_notifications_different_nw_item_should_not_get_squashed(self):
        sec_user, third_user = UserFactory(), UserFactory()
        first_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        second_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        first_notif = Notification.objects.create_nw_item_comment_notification(nw_item=first_nw_item,
                                                                               commenter=sec_user)
        second_notif = Notification.objects.create_nw_item_comment_notification(nw_item=second_nw_item,
                                                                                commenter=third_user)

        self.assertEqual(Notification.objects.filter(type=RECEIVE_NW_ITEM_COMMENT_NOTIFICATION).count(), 2)
        first_notif.refresh_from_db()
        self.assertEqual(first_notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION)
        self.assertEqualHStore(first_notif.content, self.build_content(first_nw_item, sec_user), ['nw_item_content'])
        self.assertEqual(second_notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION)
        self.assertEqual(second_notif.content, self.build_content(second_nw_item, third_user))

    def test_multiple_notifications_different_nw_items_should_get_squashed_separately(self):
        sec_user, third_user, fourth_user, fifth_user = UserFactory(), UserFactory(), UserFactory(), UserFactory()
        first_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        second_nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        for us, item_to_vote in [(sec_user, first_nw_item), (third_user, second_nw_item),
                                 (fourth_user, first_nw_item), (fifth_user, second_nw_item)]:
            notif = Notification.objects.create_nw_item_comment_notification(nw_item=item_to_vote, commenter=us)
            if us in [sec_user, third_user]:  # first commenters
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION)
                self.assertEqual(notif.content, self.build_content(item_to_vote, us))
            else:
                if us == fourth_user:
                    commenters = [sec_user, fourth_user]
                elif us == fifth_user:
                    commenters = [third_user, fifth_user]
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED)
                self.assertEqual(notif.content, self.build_squashed_content(item_to_vote, commenters))
        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_NW_ITEM_COMMENT_NOTIFICATION_SQUASHED).count(), 2)


class ReceiveChallengeCommentReplyNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.setup_proficiencies()
        self.chal = ChallengeFactory()
        self.chal_comment = ChallengeCommentFactory(challenge=self.chal, author=self.auth_user)

    def build_content(self, reply):
        return {
            'challenge_id': reply.challenge.id,
            'challenge_name': reply.challenge.name,
            'comment_id': reply.parent.id,
            'reply_id': reply.id,
            'reply_content': reply.content,
            'replier_id': reply.author.id,
            'replier_name': reply.author.username
        }

    def build_squashed_content(self, replies):
        return {
            'challenge_id': replies[0].challenge.id,
            'challenge_name': replies[0].challenge.name,
            'comment_id': replies[0].parent.id,
            'repliers': [
                {'replier_id': reply.author.id, 'replier_name': reply.author.username} for reply in replies
            ]
        }

    def test_create_notification_commenti_reply_notif(self):
        chal_reply = ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment)
        expected_content = self.build_content(chal_reply)

        notif = Notification.objects.create_challenge_comment_reply_notification(reply=chal_reply)

        self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION)
        self.assertEqual(notif.recipient, self.chal_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_notification_comment_reply_notif_not_created_if_commenter_replies_to_himself(self):
        chal_reply = ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment, author=self.auth_user)

        notif = Notification.objects.create_challenge_comment_reply_notification(reply=chal_reply)

        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_get_squashed_into_one(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment, author=us)
                   for us in [sec_user, third_user, fourth_user]]
        expected_content = self.build_squashed_content(replies)

        for reply in replies:
            notif = Notification.objects.create_challenge_comment_reply_notification(reply=reply)
            if reply != replies[0]:
                self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.chal_comment.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment, author=us)
                   for us in [sec_user, third_user, fourth_user]]

        for reply in replies:
            expected_content = self.build_content(reply)
            notif = Notification.objects.create_challenge_comment_reply_notification(reply=reply)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION)
            self.assertEqual(notif.recipient, self.chal_comment.author)
            self.assertEqual(notif.content, expected_content)

        self.assertEqual(Notification.objects.count(), 3)

    def test_two_notifications_different_comment_reply_should_not_get_squashed(self):
        sec_user, third_user = UserFactory(), UserFactory()
        self.second_chal_comment = ChallengeCommentFactory(challenge=self.chal, author=self.auth_user)
        first_reply = ChallengeCommentFactory(challenge=self.chal, parent=self.chal_comment, author=sec_user)
        second_reply = ChallengeCommentFactory(challenge=self.chal, parent=self.second_chal_comment, author=third_user)

        first_notif = Notification.objects.create_challenge_comment_reply_notification(reply=first_reply)
        second_notif = Notification.objects.create_challenge_comment_reply_notification(reply=second_reply)

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION).count(), 2)
        first_notif.refresh_from_db()
        self.assertEqualHStore(first_notif.content, self.build_content(first_reply))
        self.assertEqual(second_notif.content, self.build_content(second_reply))

    def test_multiple_notifications_different_comment_reply_should_get_squashed_separately(self):
        sec_user, third_user, fourth_user, fifth_user = UserFactory(), UserFactory(), UserFactory(), UserFactory()
        self.second_chal_comment = ChallengeCommentFactory(challenge=self.chal, author=self.auth_user)
        replies = []
        for us, comment_to_reply_on in [(sec_user, self.chal_comment), (third_user, self.second_chal_comment),
                                        (fourth_user, self.chal_comment), (fifth_user, self.second_chal_comment)]:
            reply = ChallengeCommentFactory(challenge=self.chal, parent=comment_to_reply_on, author=us)
            replies.append(reply)
            notif = Notification.objects.create_challenge_comment_reply_notification(reply=reply)
            if us in [sec_user, third_user]:  # first repliers, nothing should be squashed
                self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION)
                self.assertEqualHStore(notif.content, self.build_content(reply))
            else:
                if us == fourth_user:
                    _replies = [replies[0], replies[2]]
                elif us == fifth_user:
                    _replies = [replies[1], replies[3]]

                self.assertEqual(notif.type, RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED)
                self.assertEqualHStore(notif.content, self.build_squashed_content(_replies))

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_CHALLENGE_COMMENT_REPLY_NOTIFICATION_SQUASHED).count(), 2)


class ReceiveNWItemCommentReplyNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def build_content(self, reply):
        return {
            'nw_comment_id': reply.parent.id, 'commenter_id': reply.author.id,
            'commenter_name': reply.author.username, 'comment_content': reply.content
        }

    def build_squashed_content(self, replies):
        return {
            'nw_comment_id': replies[0].parent.id,
            'commenters': [{'commenter_id': reply.author.id, 'commenter_name': reply.author.username}
                           for reply in replies]
        }

    def test_create_nw_item_comment_reply_notif(self):
        sec_user = UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                              to_notify=False)
        reply = NewsfeedItemComment.objects.create(newsfeed_item=nw_item,
                                                   parent=nw_comment, author=sec_user,
                                                   content='secured')
        expected_content = self.build_content(reply)

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

    def test_create_multiple_notifications_should_get_squashed_into_one(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                              to_notify=False)
        replies = [NewsfeedItemComment.objects.create(newsfeed_item=nw_item, parent=nw_comment,
                                                      author=us, content='secured')
                   for us in [sec_user, third_user, fourth_user]]

        expected_content = self.build_squashed_content(replies)
        for reply in replies:
            notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=nw_comment, reply=reply)
            if reply != replies[0]:
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                              to_notify=False)
        replies = [NewsfeedItemComment.objects.create(newsfeed_item=nw_item, parent=nw_comment,
                                                      author=us, content='secured')
                   for us in [sec_user, third_user, fourth_user]]

        for reply in replies:
            notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=nw_comment, reply=reply)
            expected_content = self.build_content(reply)
            notif.is_read = True
            notif.save()
            self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)

        self.assertEqual(Notification.objects.count(), 3)

    def test_multiple_notifications_different_comment_replies_should_get_squashed_separately(self):
        sec_user, third_user, fourth_user, fifth_user = UserFactory(), UserFactory(), UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)
        first_nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                                    to_notify=False)
        second_nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                                     to_notify=False)
        replies = []
        for us, comment_to_reply in [(sec_user, first_nw_comment), (third_user, second_nw_comment),
                                     (fourth_user, first_nw_comment), (fifth_user, second_nw_comment)]:
            # expected_content = self.
            reply = NewsfeedItemComment.objects.create(newsfeed_item=nw_item, parent=comment_to_reply,
                                                       author=us, content='dominos')
            replies.append(reply)
            notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=comment_to_reply, reply=reply)

            if us in [sec_user, third_user]:
                # first repliers, nothing to get squashed with
                self.assertEqual(notif.content, self.build_content(reply))
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION)
            else:
                if us == fourth_user:
                    _replies = [replies[0], replies[2]]
                elif us == fifth_user:
                    _replies = [replies[1], replies[3]]
                self.assertEqual(notif.type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED)
                self.assertEqual(notif.content, self.build_squashed_content(_replies))
        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION_SQUASHED).count(), 2)

    def test_two_notifications_different_comment_reply_should_not_get_squashed(self):
        sec_user, third_user = UserFactory(), UserFactory()
        nw_item = NewsfeedItem.objects.create_challenge_link(challenge=ChallengeFactory(), author=self.auth_user)

        first_nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                                    to_notify=False)
        second_nw_comment: NewsfeedItemComment = nw_item.add_comment(author=self.auth_user, content='travis scott',
                                                                    to_notify=False)
        first_reply = NewsfeedItemComment.objects.create(newsfeed_item=nw_item, parent=first_nw_comment,
                                                         author=sec_user, content='secured 1')
        second_reply = NewsfeedItemComment.objects.create(newsfeed_item=nw_item, parent=second_nw_comment,
                                                         author=third_user, content='secured 2')

        first_notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=first_nw_comment,
                                                                                     reply=first_reply)
        second_notif = Notification.objects.create_nw_item_comment_reply_notification(nw_comment=second_nw_comment,
                                                                                      reply=second_reply)

        first_notif.refresh_from_db()
        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION).count(), 2)
        self.assertEqualHStore(first_notif.content, self.build_content(first_reply))
        self.assertEqual(second_notif.content, self.build_content(second_reply))


class ReceiveSubmissionCommentNotification(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.setup_proficiencies()
        self.subm = SubmissionFactory(author_id=self.auth_user.id)

    def build_content(self, comment):
        return {
            'submission_id': comment.submission.id, 'challenge_id': comment.submission.challenge.id,
            'challenge_name': comment.submission.challenge.name,
            'commenter_name': comment.author.username, 'comment_content': comment.content,
            'comment_id': comment.id, 'commenter_id': comment.author.id,
        }

    def build_squashed_content(self, comments):
        return {
            'submission_id': comments[0].submission.id, 'challenge_id': comments[0].submission.challenge.id,
            'challenge_name': comments[0].submission.challenge.name,
            'commenters': [
                {'commenter_name': subm_comment.author.username, 'commenter_id': subm_comment.author.id}
                for subm_comment in comments
            ]
        }

    def test_create_submission_comment_notification(self):
        subm_comment = SubmissionCommentFactory(submission=self.subm)
        expected_content = self.build_content(subm_comment)

        notif = Notification.objects.create_submission_comment_notification(comment=subm_comment)
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)
        self.assertEqual(notif.recipient, self.subm.author)
        self.assertEqual(notif.content, expected_content)

    def test_create_submission_comment_notification_not_created_if_author_comments_himself(self):
        subm_comment = SubmissionCommentFactory(submission=self.subm, author=self.auth_user)
        notif = Notification.objects.create_submission_comment_notification(comment=subm_comment)
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_multiple_notifications_should_get_squashed_into_one(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        comments = [self.subm.add_comment(us, 'x', to_notify=False) for us in [sec_user, third_user, fourth_user]]
        expected_content = self.build_squashed_content(comments)

        for comment in comments:
            notif = Notification.objects.create_submission_comment_notification(comment=comment)
            if comment != comments[0]:
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(notif.content, expected_content)

    def test_create_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        comments = [self.subm.add_comment(us, 'x', to_notify=False) for us in [sec_user, third_user, fourth_user]]

        for comment in comments:
            expected_content = self.build_content(comment)
            notif = Notification.objects.create_submission_comment_notification(comment=comment)
            notif.is_read = True
            notif.save()

            self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)
            self.assertEqual(notif.recipient, self.auth_user)
            self.assertEqual(notif.content, expected_content)

        self.assertEqual(Notification.objects.count(), 3)

    def test_two_notifications_different_submissions_should_not_get_squashed(self):
        sec_user = UserFactory()
        self.second_subm = SubmissionFactory(author_id=self.auth_user.id)
        first_comment = SubmissionCommentFactory(submission=self.subm, author=sec_user)
        second_comment = SubmissionCommentFactory(submission=self.second_subm, author=sec_user)

        first_notif = Notification.objects.create_submission_comment_notification(comment=first_comment)
        second_notif = Notification.objects.create_submission_comment_notification(comment=second_comment)

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_SUBMISSION_COMMENT_NOTIFICATION).count(), 2)
        first_notif.refresh_from_db()
        self.assertEqualHStore(first_notif.content, self.build_content(first_comment))
        self.assertEqual(second_notif.content, self.build_content(second_comment))

    def test_multiple_notifications_two_different_submissions_should_get_squashed_separately(self):
        sec_user, third_user, fourth_user, fifth_user = UserFactory(), UserFactory(), UserFactory(), UserFactory()
        self.second_subm = SubmissionFactory(author_id=self.auth_user.id)
        comments = []
        for us, subm_to_comment in [(sec_user, self.subm), (third_user, self.second_subm),
                                    (fourth_user, self.subm), (fifth_user, self.second_subm)]:
            comment = SubmissionCommentFactory(submission=subm_to_comment, author=us)
            comments.append(comment)
            notif = Notification.objects.create_submission_comment_notification(comment=comment)
            if us in [sec_user, third_user]:
                # first commenters, nothing to squash with
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)
                self.assertEqual(notif.content, self.build_content(comment))
            else:
                if us == fourth_user:
                    _comments = [comments[0], comments[2]]
                elif us == fifth_user:
                    _comments = [comments[1], comments[3]]
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED)
                self.assertEqual(notif.content, self.build_squashed_content(_comments))

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_SUBMISSION_COMMENT_NOTIFICATION_SQUASHED).count(), 2)


class ReceiveSubmissionCommentReplyNotificationTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.setup_proficiencies()
        self.subm = SubmissionFactory(author_id=self.auth_user.id)
        self.subm_comment = SubmissionCommentFactory(submission=self.subm, author=self.auth_user)

    def build_content(self, reply):
        return {
            'submission_id': reply.submission.id, 'challenge_id': reply.submission.challenge.id,
            'challenge_name': reply.submission.challenge.name, 'comment_id': reply.id,
            'comment_content': reply.content, 'commenter_id': reply.author.id,
            'commenter_name': reply.author.username
        }

    def build_squashed_content(self, replies):
        return {
            'submission_id': replies[0].submission.id, 'challenge_id': replies[0].submission.challenge.id,
            'challenge_name': replies[0].submission.challenge.name,
            'commenters': [
                {
                    'commenter_id': reply.author.id,
                    'commenter_name': reply.author.username
                } for reply in replies
            ]
        }

    def test_create_submission_comment_reply_notif(self):
        sec_user = UserFactory()
        subm_reply = SubmissionCommentFactory(submission=self.subm, author=sec_user, parent=self.subm_comment)
        expected_content = self.build_content(subm_reply)

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

    def test_create_multiple_notifications_should_get_squashed_into_one(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [SubmissionCommentFactory(submission=self.subm, author=us, parent=self.subm_comment)
                   for us in [sec_user, third_user, fourth_user]]
        expected_content = self.build_squashed_content(replies)
        for reply in replies:
            notif = Notification.objects.create_submission_comment_reply_notification(comment=reply)
            if reply != replies[0]:
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED)
        self.assertEqual(notif.content, expected_content)
        self.assertEqual(notif.recipient, self.auth_user)

    def test_create_multiple_notifications_should_not_get_squashed_if_read_consecutively(self):
        sec_user, third_user, fourth_user = UserFactory(), UserFactory(), UserFactory()
        replies = [SubmissionCommentFactory(submission=self.subm, author=us, parent=self.subm_comment)
                   for us in [sec_user, third_user, fourth_user]]

        for reply in replies:
            notif = Notification.objects.create_submission_comment_reply_notification(comment=reply)
            expected_content = self.build_content(reply)

            self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION)
            self.assertEqual(notif.content, expected_content)
            self.assertEqual(notif.recipient, self.auth_user)
        self.assertEqual(Notification.objects.count(), 3)

    def test_two_notifications_different_comment_reply_should_not_get_squashed(self):
        sec_user = UserFactory()
        self.second_subm_comment = SubmissionCommentFactory(submission=self.subm, author=self.auth_user)
        first_reply = SubmissionCommentFactory(submission=self.subm, author=sec_user, parent=self.subm_comment)
        second_reply = SubmissionCommentFactory(submission=self.subm, author=sec_user, parent=self.second_subm_comment)

        first_notif = Notification.objects.create_submission_comment_reply_notification(comment=first_reply)
        second_notif = Notification.objects.create_submission_comment_reply_notification(comment=second_reply)

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION).count(), 2)
        first_notif.refresh_from_db()
        self.assertEqualHStore(first_notif.content, self.build_content(first_reply))
        self.assertEqual(second_notif.content, self.build_content(second_reply))

    def test_multiple_notifications_two_different_comments_should_get_squashed_separately(self):
        sec_user, third_user, fourth_user, fifth_user = UserFactory(), UserFactory(), UserFactory(), UserFactory()
        self.second_subm_comment = SubmissionCommentFactory(submission=self.subm, author=self.auth_user)
        replies = []
        for us, comment_to_reply in [(sec_user, self.subm_comment), (third_user, self.second_subm_comment),
                                     (fourth_user, self.subm_comment), (fifth_user, self.second_subm_comment)]:
            reply = SubmissionCommentFactory(submission=self.subm, author=sec_user, parent=comment_to_reply)
            replies.append(reply)
            notif = Notification.objects.create_submission_comment_reply_notification(comment=reply)

            if us in [sec_user, third_user]:
                # first repliers, nothing to squash with
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION)
                self.assertEqual(notif.content, self.build_content(reply))
            else:
                if us == fourth_user:
                    _replies = [replies[0], replies[2]]
                elif us == fifth_user:
                    _replies = [replies[1], replies[3]]
                self.assertEqual(notif.type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED)
                self.assertEqual(notif.content, self.build_squashed_content(_replies))

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(Notification.objects.filter(type=RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION_SQUASHED).count(), 2)


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
