from datetime import timedelta, datetime

import jwt
from rest_framework.test import APITestCase

from accounts.constants import NOTIFICATION_TOKEN_EXPIRY_MINUTES, NOTIFICATION_SECRET_KEY
from challenges.tests.base import TestHelperMixin


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
