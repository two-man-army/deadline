from unittest.mock import MagicMock, patch

from django.test import TestCase

from challenges.tests.factories import UserFactory
from private_chat.constants import EXPIRED_TOKEN_ERR_TYPE, AUTHORIZATION_ERR_TYPE, VALIDATION_ERR_TYPE
from private_chat.handlers import _authenticate, _new_messages_handler, _is_typing
from private_chat.models import Dialog, Message


class AuthenticateTests(TestCase):
    def setUp(self):
        self.first_user = UserFactory()
        self.second_user = UserFactory()

    def test_returns_token_and_validates_websocket(self):
        """
        On a successful authentication, the user's websocket must be marked as valid
        :return:
        """
        websocket_mock = MagicMock(is_valid=False)
        ws_connections = {(self.first_user.id, self.second_user.id): websocket_mock}
        with patch('private_chat.handlers.ws_connections', ws_connections):
            to_send_message, payload = _authenticate({'auth_token': self.first_user.auth_token.key},
                                                           self.first_user.id, self.second_user.id)

            self.assertTrue(to_send_message)
            self.assertEqual(payload['type'], 'OK')
            self.assertEqual(websocket_mock.is_valid, True)

    def test_returns_error_if_invalid_token(self):
        websocket_mock = MagicMock(is_valid=False)
        ws_connections = {(self.first_user.id, self.second_user.id): websocket_mock}
        with patch('private_chat.handlers.ws_connections', {(self.first_user.id, self.second_user.id): ws_connections}):
            to_send_message, payload = _authenticate({'auth_token': 'sELEMENT'},
                                                           self.first_user.id, self.second_user.id)

            self.assertTrue(to_send_message)
            self.assertEqual('error', payload['type'])
            self.assertEqual(AUTHORIZATION_ERR_TYPE, payload['error_type'])
            self.assertEqual(websocket_mock.is_valid, False)


class NewsMessageTests(TestCase):
    def setUp(self):
        self.first_user = UserFactory()
        self.second_user = UserFactory()

    def test_creates_message(self):
        dialog: Dialog = Dialog.objects.get_or_create_dialog_with_users(self.first_user, self.second_user)
        packet = {
            'message': 'Hello Bob :)',
            'conversation_token': dialog.owner_token
        }

        with patch('private_chat.handlers.ws_connections',
                   {(self.first_user.id, self.second_user.id): MagicMock(is_valid=True)}):
            to_send_msg, is_err, payload = _new_messages_handler(packet, self.first_user.id, self.second_user.id)

            self.assertTrue(to_send_msg)
            self.assertFalse(is_err)
            self.assertEqual(Message.objects.count(), 1)
            msg = Message.objects.first()
            self.assertEqual(msg.text, 'Hello Bob :)')
            self.assertEqual(msg.sender, self.first_user)
            expected_payload = {
                'type': 'received-message',
                'created': msg.get_formatted_create_datetime(),
                'sender_name': msg.sender.username,
                'message': 'Hello Bob :)',
                'id': msg.id
            }
            self.assertEqual(expected_payload, payload)

    def test_sends_error_if_message_is_empty(self):
        packet = {
            'conversation_token': 'tank'
        }
        with patch('private_chat.handlers.ws_connections',
                   {(self.first_user.id, self.second_user.id): MagicMock(is_valid=True)}):
            to_send_msg, is_err, payload = _new_messages_handler(packet, self.first_user.id, self.second_user.id)
            self.assertTrue(to_send_msg)
            self.assertTrue(is_err)
            self.assertEqual('error', payload['type'])
            self.assertEqual(VALIDATION_ERR_TYPE, payload['error_type'])
            self.assertIn('message', payload['message'].lower())

    def test_doesnt_send_message_if_websocket_not_available(self):
        to_send_msg, is_err, payload = _new_messages_handler({}, self.first_user.id, 200)
        self.assertFalse(to_send_msg)
        self.assertTrue(is_err)

    def test_sends_error_if_websocket_is_not_valid(self):
        packet = {
            'conversation_token': 'tank',
            'message': ' TANK'
        }
        with patch('private_chat.handlers.ws_connections',
                   {(self.first_user.id, self.second_user.id): MagicMock(is_valid=False)}):
            to_send_msg, is_err, payload = _new_messages_handler(packet, self.first_user.id, self.second_user.id)
            self.assertTrue(to_send_msg)
            self.assertTrue(is_err)
            self.assertEqual('error', payload['type'])
            self.assertEqual(AUTHORIZATION_ERR_TYPE, payload['error_type'])


class IsTypingTests(TestCase):
    def setUp(self):
        self.first_user = UserFactory()
        self.second_user = UserFactory()

    def test_doesnt_send_message_if_websocket_not_available(self):
        to_send_msg, payload = _is_typing(self.first_user.id, 200, 'what')
        self.assertFalse(to_send_msg)

    def test_sends_error_if_websocket_is_not_valid(self):
        with patch('private_chat.handlers.ws_connections',
                   {(self.first_user.id, self.second_user.id): MagicMock(is_valid=False)}):
            to_send_msg, payload = _is_typing(self.first_user.id, self.second_user.id, 'TANK')
            self.assertTrue(to_send_msg)
            self.assertTrue(payload['type'], 'error')
            self.assertEqual(AUTHORIZATION_ERR_TYPE, payload['error_type'])

    def test_doesnt_send_message_if_all_ok(self):
        dialog = Dialog.objects.get_or_create_dialog_with_users(self.first_user, self.second_user)
        with patch('private_chat.handlers.ws_connections',
                   {(self.first_user.id, self.second_user.id): MagicMock(is_valid=True)}):
            to_send_msg, payload = _is_typing(self.first_user.id, self.second_user.id, dialog.owner_token)
            self.assertFalse(to_send_msg)
