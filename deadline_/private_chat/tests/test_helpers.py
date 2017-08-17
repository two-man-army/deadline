from datetime import datetime, timedelta
from unittest import TestCase as unittest_TestCase
from unittest.mock import patch, MagicMock

from private_chat.constants import DIALOG_TOKEN_EXPIRY_MINUTES
from private_chat.errors import RegexMatchError
from private_chat.helpers import extract_connect_path, generate_dialog_tokens


class ExtractPathTests(unittest_TestCase):
    def test_normal_path_returns_expected(self):
        owner_token = 'a241rfv134fma3'
        owner_id = 1111
        opponent_id = 1
        path = f'/{owner_id}/{owner_token}/{opponent_id}'

        rec_owner_id, rec_owner_token, rec_opponent_id = extract_connect_path(path)
        self.assertIsInstance(rec_owner_id, int)
        self.assertIsInstance(rec_opponent_id, int)
        self.assertEqual(rec_owner_token, owner_token)
        self.assertEqual(rec_owner_id, owner_id)
        self.assertEqual(rec_opponent_id, opponent_id)

    def test_various_wrong_paths_throws_regex_match_error(self):
        wrong_paths = [
            '1/213f/1',  # no slash at start
            '1231f/13',
            '/12/141341AA41/13'  # capital letters
            '/1231/1413#$#$/14',  # symbols
            '/41431/431fa13/4g'
            'd/41431/431fa13/4'
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
