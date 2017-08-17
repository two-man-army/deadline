from unittest.mock import patch

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
