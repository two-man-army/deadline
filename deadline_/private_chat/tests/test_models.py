from datetime import datetime, timedelta
from time import sleep
from unittest.mock import patch
import jwt

from django.test import TestCase
from radar import random_datetime

from challenges.tests.factories import UserFactory
from private_chat.models import Dialog, Message
from private_chat.serializers import MessageSerializer


class DialogModelTests(TestCase):
    @patch('private_chat.models.generate_dialog_tokens')
    def test_creation_assigns_secret_key_and_tokens(self, mock_gen_tokens):
        mock_gen_tokens.return_value = ('one', 'two', 'three')
        owner_name, opponent_name = 'owner', 'opponent'
        owner, opponent = UserFactory(username=owner_name), UserFactory(username=opponent_name)
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)

        self.assertEqual(dialog.secret_key, 'one')
        self.assertEqual(dialog.owner_token, 'two')
        self.assertEqual(dialog.opponent_token, 'three')
        mock_gen_tokens.assert_called_once_with(owner_name, opponent_name)

    def test_tokens_are_expired(self):
        owner_name, opponent_name = 'owner', 'opponent'
        owner, opponent = UserFactory(username=owner_name), UserFactory(username=opponent_name)
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)

        self.assertFalse(dialog.tokens_are_expired())

    def test_tokens_are_expired_expired_token_should_return_false(self):
        owner_name, opponent_name = 'owner', 'opponent'
        owner, opponent = UserFactory(username=owner_name), UserFactory(username=opponent_name)
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)
        dialog.opponent_token = jwt.encode({'exp': datetime.utcnow() - timedelta(minutes=1), 'username': opponent_name}, dialog.secret_key)
        dialog.save()

        self.assertTrue(dialog.tokens_are_expired())

    @patch('private_chat.models.Dialog.tokens_are_expired')
    def test_token_is_valid(self, mock_tokens_are_expired):
        mock_tokens_are_expired.return_value = False

        owner_name, opponent_name = 'owner', 'opponent'
        owner, opponent = UserFactory(username=owner_name), UserFactory(username=opponent_name)
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)

        self.assertTrue(dialog.token_is_valid(dialog.opponent_token))
        mock_tokens_are_expired.assert_called_once()
        self.assertTrue(dialog.token_is_valid(dialog.owner_token))

    def test_token_is_valid_forged_token_should_return_false(self):
        # creating a separate token with the same username should not be a valid token
        owner_name, opponent_name = 'owner', 'opponent'
        owner, opponent = UserFactory(username=owner_name), UserFactory(username=opponent_name)
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)
        owner_token = jwt.encode({'exp': datetime.utcnow() + timedelta(days=1), 'username': owner_name}, dialog.secret_key)
        opponent_token = jwt.encode({'exp': datetime.utcnow() + timedelta(days=1), 'username': opponent_name}, dialog.secret_key)

        self.assertFalse(dialog.token_is_valid(opponent_token))
        self.assertFalse(dialog.token_is_valid(owner_token))

    @patch('private_chat.models.Dialog.tokens_are_expired')
    def test_refresh_tokens_expired_tokens_should_refresh(self, mock_are_expired):
        mock_are_expired.return_value = False
        owner, opponent = UserFactory(username='own'), UserFactory(username='opn')
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)
        with patch('private_chat.models.generate_dialog_tokens') as mock_gen:
            mock_gen.return_value = '1', '2', '3'

            dialog.refresh_tokens()
            self.assertEqual(dialog.secret_key, '1')
            self.assertEqual(dialog.owner_token, '2')
            self.assertEqual(dialog.opponent_token, '3')
            mock_are_expired.assert_called_once()
            mock_gen.assert_called_once_with('own', 'opn')

    @patch('private_chat.models.Dialog.tokens_are_expired')
    def test_force_refresh_tokens_expired_tokens_should_refresh(self, mock_are_expired):
        mock_are_expired.return_value = False
        owner, opponent = UserFactory(username='own'), UserFactory(username='opn')
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)

        with patch('private_chat.models.generate_dialog_tokens') as mock_gen:
            mock_gen.return_value = '1', '2', '3'

            dialog.refresh_tokens(force=True)
            self.assertEqual(dialog.secret_key, '1')
            self.assertEqual(dialog.owner_token, '2')
            self.assertEqual(dialog.opponent_token, '3')
            mock_gen.assert_called_once_with('own', 'opn')

    @patch('private_chat.models.Dialog.tokens_are_expired')
    def test_refresh_tokens_not_expired_tokens_should_raise(self, mock_are_expired):
        mock_are_expired.return_value = True
        owner, opponent = UserFactory(username='own'), UserFactory(username='opn')
        dialog = Dialog.objects.create(owner=owner, opponent=opponent)

        with self.assertRaises(Exception):
            dialog.refresh_tokens()

    def test_get_or_create_dialog_should_get_existing_dialog(self):
        # Should get the existing dialog regardless of how we send the users
        owner, opponent = UserFactory(), UserFactory()

        dialog = Dialog.objects.create(owner=owner, opponent=opponent)

        self.assertEqual(dialog, Dialog.objects.get_or_create_dialog_with_users(owner, opponent))
        self.assertEqual(dialog, Dialog.objects.get_or_create_dialog_with_users(opponent, owner))

    def test_get_or_create_dialog_should_create_dialog_when_it_doesnt_exist(self):
        owner, opponent = UserFactory(), UserFactory()

        dialog = Dialog.objects.get_or_create_dialog_with_users(owner, opponent)

        self.assertEqual(dialog.owner, owner)
        self.assertEqual(dialog.opponent, opponent)


class MessageModelTests(TestCase):
    def setUp(self):
        self.first_user = UserFactory()
        self.second_user = UserFactory()
        self.dialog = Dialog.objects.create(owner=self.first_user, opponent=self.second_user)

    def test_serializes(self):
        msg = Message.objects.create(dialog=self.dialog, sender=self.first_user, text='What the f you mean?')
        ser_data = MessageSerializer(instance=msg).data
        expected_data = {
            'id': msg.id,
            'message': 'What the f you mean?',
            'sender_name': self.first_user.username,
            'created': msg.get_formatted_create_datetime()
        }

        self.assertEqual(ser_data, expected_data)

    def test_many_serialize_are_ordered_by_date(self):
        for i in range(10):
            Message.objects.create(dialog=self.dialog, sender=self.first_user, text='What the f you mean?',
                                   created=random_datetime())
        ordered_message_ids = [p['id'] for p in Message.objects.order_by('created').values('id').all()]
        received_ordered_ids = [p['id'] for p in MessageSerializer(instance=Message.objects.all(), many=True).data]
        self.assertEqual(ordered_message_ids, received_ordered_ids)
