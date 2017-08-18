import asyncio
from unittest.mock import MagicMock, patch

from django.test import TestCase

from challenges.tests.factories import UserFactory
from private_chat.handlers import _fetch_dialog_token
from private_chat.models import Dialog
from private_chat.services.dialog import get_or_create_dialog_token


class FetchDialogTokenTests(TestCase):
    def setUp(self):
        self.first_user = UserFactory()
        self.second_user = UserFactory()

    def test_returns_token(self):
        with patch('private_chat.handlers.ws_connections', {(self.first_user.id, self.second_user.id): 1}):
            to_send_message, payload = _fetch_dialog_token({'auth_token': self.first_user.auth_token.key},
                                                           self.first_user.id, self.second_user.id)

            expected_token = Dialog.objects.get_or_create_dialog_with_users(self.first_user, self.second_user).owner_token
            self.assertTrue(to_send_message)
            self.assertEqual(payload, {'conversation_token': bytes(expected_token, 'utf-8')})  # no idea why it turns into bytes

    def test_returns_false_if_ids_not_in_ws_connections(self):
        """
        We do not have the users' connection, therefore its pointless to process it
        :return:
        """
        with patch('private_chat.handlers.ws_connections', {(22, 22): 1}):
            to_send_message, payload = _fetch_dialog_token({'auth_token': self.first_user.auth_token.key},
                                                           self.first_user.id, self.second_user.id)
            self.assertFalse(to_send_message)
            self.assertEqual(payload, {})

    def test_returns_error_if_invalid_token(self):
        with patch('private_chat.handlers.ws_connections', {(self.first_user.id, self.second_user.id): 1}):
            to_send_message, payload = _fetch_dialog_token({'auth_token': 'sELEMENT'},
                                                           self.first_user.id, self.second_user.id)

            self.assertTrue(to_send_message)
            self.assertIn('error', payload)
