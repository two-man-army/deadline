from datetime import timedelta, datetime
from unittest.mock import patch

import jwt
from rest_framework.test import APITestCase

from accounts.constants import NOTIFICATION_TOKEN_EXPIRY_MINUTES, NOTIFICATION_SECRET_KEY
from challenges.tests.base import TestHelperMixin


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
    def test_callsserializer_and_fetch_method(self, mock_fetch, mock_serializer):
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
