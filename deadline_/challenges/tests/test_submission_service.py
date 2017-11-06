from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import datetime

from challenges.services.submissions import submissions_count_by_date_from_user_since


class SubmissionServiceTests(TestCase):
    @patch('challenges.services.submissions.Submission.fetch_submissions_count_from_user_since')
    def test_submissions_count_by_date_for_user_since_maps_as_expected_and_ignores_empty_count(self, fetch_mock):
        date_one, date_two, date_three = datetime(2017, 10, 12), datetime(2017, 10, 13), datetime(2012, 10, 12)
        fetch_mock.return_value = [
            {'created_at': date_one, 'count': 15},
            {'created_at': date_two, 'count': 0},
            {'created_at': date_three, 'count': 3}
        ]
        expected_data = {
            date_one: 15,
            date_three: 3
        }
        user_mock = MagicMock('user')

        received_data = submissions_count_by_date_from_user_since(user_mock, date_one)

        fetch_mock.assert_called_once_with(user_mock, date_one)
        self.assertEqual(expected_data, received_data)
