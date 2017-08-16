from unittest import TestCase as unittest_TestCase

from private_chat.errors import RegexMatchError
from private_chat.helpers import extract_connect_path


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
