from datetime import datetime, timedelta
from unittest.mock import patch
import jwt

from django.test import TestCase

from challenges.tests.factories import UserFactory
from private_chat.models import Dialog


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
