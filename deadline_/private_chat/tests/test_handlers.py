from unittest.mock import MagicMock, patch

from django.test import TestCase

from challenges.tests.factories import UserFactory
from private_chat.handlers import _fetch_dialog_token, _new_messages_handler
from private_chat.models import Dialog, Message


class FetchDialogTokenTests(TestCase):
    def setUp(self):
        self.first_user = UserFactory()
        self.second_user = UserFactory()

    def test_returns_token_and_validates_websocket(self):
        websocket_mock = MagicMock(is_valid=False)
        ws_connections = {(self.first_user.id, self.second_user.id): websocket_mock}
        with patch('private_chat.handlers.ws_connections', ws_connections):
            to_send_message, payload = _fetch_dialog_token({'auth_token': self.first_user.auth_token.key},
                                                           self.first_user.id, self.second_user.id)

            expected_token = Dialog.objects.get_or_create_dialog_with_users(self.first_user, self.second_user).owner_token
            self.assertTrue(to_send_message)
            self.assertEqual(payload, {'conversation_token': expected_token})
            self.assertEqual(websocket_mock.is_valid, True)

    def test_returns_false_if_ids_not_in_ws_connections(self):
        """
        We do not have the users' connection, therefore its pointless to process it
        :return:
        """
        websocket_mock = MagicMock(is_valid=False)
        ws_connections = {(22, 22): websocket_mock}
        with patch('private_chat.handlers.ws_connections', ws_connections):
            to_send_message, payload = _fetch_dialog_token({'auth_token': self.first_user.auth_token.key},
                                                           self.first_user.id, self.second_user.id)
            self.assertFalse(to_send_message)
            self.assertEqual(payload, {})
            self.assertEqual(websocket_mock.is_valid, False)

    def test_returns_error_if_invalid_token(self):
        websocket_mock = MagicMock(is_valid=False)
        ws_connections = {(self.first_user.id, self.second_user.id): websocket_mock}
        with patch('private_chat.handlers.ws_connections', {(self.first_user.id, self.second_user.id): ws_connections}):
            to_send_message, payload = _fetch_dialog_token({'auth_token': 'sELEMENT'},
                                                           self.first_user.id, self.second_user.id)

            self.assertTrue(to_send_message)
            self.assertIn('error', payload)
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
            self.assertIn('message', payload['error'].lower())

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
            self.assertIn('authorize', payload['error'].lower())

    def test_sends_error_if_dialog_invalid(self):
        packet = {
            'conversation_token': 'tank',
            'message': ' TANK'
        }
        with patch('private_chat.handlers.ws_connections',
                   {(self.first_user.id, self.second_user.id): MagicMock(is_valid=True)}):
            to_send_msg, is_err, payload = _new_messages_handler(packet, self.first_user.id, self.second_user.id)
            self.assertTrue(to_send_msg)
            self.assertTrue(is_err)
            self.assertIn('token', payload['error'].lower())
