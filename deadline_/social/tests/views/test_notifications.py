from datetime import timedelta, datetime
from unittest import TestCase as unittest_TestCase
from unittest.mock import patch

import jwt
from rest_framework.test import APITestCase

from accounts.constants import NOTIFICATION_TOKEN_EXPIRY_MINUTES, NOTIFICATION_SECRET_KEY
from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import ChallengeFactory, UserFactory
from social.models.notification import Notification
from social.views import NotificationManageView, unseen_notifications, NotificationReadView


class NotificationManageViewTests(unittest_TestCase):
    def test_defines_appropriate_views(self):
        self.assertEqual(len(NotificationManageView.VIEWS_BY_METHOD.keys()), 2)
        self.assertEqual(NotificationManageView.VIEWS_BY_METHOD['GET'](), unseen_notifications)
        self.assertEqual(NotificationManageView.VIEWS_BY_METHOD['PUT'], NotificationReadView.as_view)


class UnseenNotificationsViewTests(APITestCase, TestHelperMixin):
    """ The unseen notifications view
        should return all the notifications for a given user that are not marked as is_read"""
    def setUp(self):
        self.create_user_and_auth_token()

    def test_requires_auth(self):
        resp = self.client.get('/social/notifications/')
        self.assertEqual(resp.status_code, 401)

    @patch('social.views.NotificationSerializer')
    @patch('social.views.Notification.fetch_unread_notifications_for_user')
    def test_calls_serializer_and_fetch_method(self, mock_fetch, mock_serializer):
        mock_serializer.data = 'hello'
        mock_serializer.return_value = mock_serializer
        mock_fetch.return_value = 'fetched'

        resp = self.client.get('/social/notifications/', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, 'hello')
        mock_serializer.assert_called_once_with(instance='fetched', many=True)
        mock_fetch.assert_called_once_with(self.auth_user)


class NotificationTokenViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_creates_token(self):
        response = self.client.get('/social/notifications/token', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['token'], self.auth_user.notification_token)

    def test_requires_auth(self):
        response = self.client.get('/social/notifications/token')
        self.assertEqual(response.status_code, 401)

    def test_creates_new_token_if_expired(self):
        expiry_date = datetime.utcnow() - timedelta(minutes=NOTIFICATION_TOKEN_EXPIRY_MINUTES)
        expired_token = jwt.encode({'exp': expiry_date, 'username': self.auth_user.username}, NOTIFICATION_SECRET_KEY).decode('utf-8')
        self.auth_user.notification_token = expired_token
        self.auth_user.save()
        self.assertTrue(self.auth_user.notification_token_is_expired())

        response = self.client.get('/social/notifications/token', HTTP_AUTHORIZATION=self.auth_token)

        self.auth_user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(expired_token, self.auth_user.notification_token)
        self.assertEqual(response.data['token'], self.auth_user.notification_token)


class NotificationReadViewTests(APITestCase, TestHelperMixin):
    """
    The NotificationRead view must
    """
    def setUp(self):
        self.create_user_and_auth_token()

    def test_updates_notification(self):
        chal = ChallengeFactory()
        notifs = [Notification.objects.create_new_challenge_notification(
            recipient=self.auth_user, challenge=chal) for _ in range(20)]
        resp = self.client.put('/social/notifications/', HTTP_AUTHORIZATION=self.auth_token,
                               data={'notifications': [n.id for n in notifs]}, format='json')

        self.assertEqual(resp.status_code, 200)
        for notif in notifs:
            notif.refresh_from_db()
            self.assertTrue(notif.is_read)

    def test_does_not_update_for_notifications_that_are_not_the_users(self):
        sec_user = UserFactory()
        chal = ChallengeFactory()
        notifs = [
            Notification.objects.create_new_challenge_notification(
                recipient=self.auth_user if i % 2 == 0 else sec_user, challenge=chal)
            for i in range(20)]

        resp = self.client.put('/social/notifications/', HTTP_AUTHORIZATION=self.auth_token,
                               data={'notifications': [n.id for n in notifs]}, format='json')

        self.assertEqual(resp.status_code, 200)
        # Assert that only the notifs by the user were changed
        for notif in notifs:
            notif.refresh_from_db()
            if notif.recipient == self.auth_user:
                self.assertTrue(notif.is_read)
            else:
                self.assertFalse(notif.is_read)

    def test_requires_auth(self):
        resp = self.client.put('/social/notifications/')
        self.assertEqual(resp.status_code, 401)
