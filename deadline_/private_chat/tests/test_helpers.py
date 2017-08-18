from datetime import datetime, timedelta
from unittest import TestCase as unittest_TestCase
from unittest.mock import patch, MagicMock

from challenges.tests.factories import UserFactory
from private_chat.constants import DIALOG_TOKEN_EXPIRY_MINUTES
from private_chat.errors import RegexMatchError
from private_chat.helpers import extract_connect_path, generate_dialog_tokens
from private_chat.services.dialog import get_or_create_dialog_token


class ExtractPathTests(unittest_TestCase):
    def test_normal_path_returns_expected(self):
        owner_id = 1111
        opponent_id = 1
        path = f'/chat/{owner_id}/{opponent_id}'

        rec_owner_id, rec_opponent_id = extract_connect_path(path)
        self.assertIsInstance(rec_owner_id, int)
        self.assertIsInstance(rec_opponent_id, int)
        self.assertEqual(rec_owner_id, owner_id)
        self.assertEqual(rec_opponent_id, opponent_id)

    def test_various_wrong_paths_throws_regex_match_error(self):
        wrong_paths = [
            'chat/1/1',  # no slash at start
            'chat/1231f/13',
            '/chat/1231/14.1',  # symbols
            '/chat/chat/41431/4g'
            'd/41431/1/431fa13/4'
        ]
        for path in wrong_paths:
            with self.assertRaises(RegexMatchError):
                extract_connect_path(path)


class GenerateDialogTokensTests(unittest_TestCase):
    """
    generate_dialog_tokens should get a secret key from uuid4, call jwt encode and return them
    """

    @patch('private_chat.helpers.uuid4')
    @patch('private_chat.helpers.get_utc_time')
    @patch('private_chat.helpers.jwt.encode')
    def test_works_correctly(self, mock_jwt_encode, mock_utc_time, mock_uuid4):
        """
        Should get a secret key, an expiry date and create a JWT with them
        """
        mock_uuid4.return_value = MagicMock(hex='secret')
        utc_time = datetime.utcnow()
        mock_utc_time.return_value = utc_time
        mock_jwt_encode.return_value = 1
        owner_name, opponent_name = 'owner', 'opponent'
        expected_expiry_date = utc_time + timedelta(minutes=DIALOG_TOKEN_EXPIRY_MINUTES)

        received_secret, received_owner_token, received_opponent_token = generate_dialog_tokens(owner_name, opponent_name)

        mock_jwt_encode.assert_any_call({'exp': expected_expiry_date, 'username': owner_name}, 'secret')
        mock_jwt_encode.assert_any_call({'exp': expected_expiry_date, 'username': opponent_name}, 'secret')
        self.assertEqual(received_secret, 'secret')
        self.assertEqual(received_opponent_token, 1)
        self.assertEqual(received_owner_token, 1)


class GetOrCreateDialogTokenTests(unittest_TestCase):
    def setUp(self):
        self.first_user = UserFactory()
        self.second_user = UserFactory()

    @patch('private_chat.services.dialog.Dialog.objects.get_or_create_dialog_with_users')
    def test_gets_owner_token_if_owner_passed(self, mock_goc_dialog_users):
        tokens_are_expired = MagicMock()
        tokens_are_expired.return_value = False
        mock_goc_dialog_users.return_value = MagicMock(
            tokens_are_expired=tokens_are_expired,
            owner_token='token',
            owner=self.first_user
        )

        token = get_or_create_dialog_token(owner=self.first_user, opponent=self.second_user)
        self.assertEqual(token, 'token')

        tokens_are_expired.assert_called_once()
        mock_goc_dialog_users.assert_called_once_with(self.first_user, self.second_user)

    @patch('private_chat.services.dialog.Dialog.objects.get_or_create_dialog_with_users')
    def test_gets_opponent_token_if_owner_is_opponent_on_dialog(self, mock_goc_dialog_users):
        tokens_are_expired = MagicMock()
        tokens_are_expired.return_value = False
        mock_goc_dialog_users.return_value = MagicMock(
            tokens_are_expired=tokens_are_expired,
            opponent_token='token',
            opponent=self.first_user
        )

        token = get_or_create_dialog_token(owner=self.first_user, opponent=self.second_user)
        self.assertEqual(token, 'token')

        tokens_are_expired.assert_called_once()
        mock_goc_dialog_users.assert_called_once_with(self.first_user, self.second_user)

    @patch('private_chat.services.dialog.Dialog.objects.get_or_create_dialog_with_users')
    def test_calls_refresh_tokens_if_expired(self, mock_goc_dialog_users):
        tokens_are_expired = MagicMock()
        tokens_are_expired.return_value = True
        refresh_tokens = MagicMock()
        mock_goc_dialog_users.return_value = MagicMock(
            tokens_are_expired=tokens_are_expired,
            refresh_tokens=refresh_tokens,
            opponent_token='token',
            opponent=self.first_user
        )

        token = get_or_create_dialog_token(owner=self.first_user, opponent=self.second_user)

        self.assertEqual(token, 'token')
        tokens_are_expired.assert_called_once()
        refresh_tokens.assert_called_once()
        mock_goc_dialog_users.assert_called_once_with(self.first_user, self.second_user)
