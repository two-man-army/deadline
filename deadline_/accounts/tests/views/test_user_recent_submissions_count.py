from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase

from challenges.tests.base import TestHelperMixin


@patch('accounts.views.datetime_now')
@patch('accounts.views.submissions_count_by_date_from_user_since')
class UserRecentSubmissionsCountView(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.now_date = datetime.now()

    def test_weekly_counts_seven_days_from_now(self, subm_count_mock, dt_now):
        dt_now.return_value = self.now_date
        subm_count_mock.return_value = {'x': 'x'}
        expected_since_date = self.now_date - timedelta(days=7)

        response = self.client.get(f'/accounts/user/{self.auth_user.id}/recent_submissions?date_mode=weekly',
                                   HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'x': 'x'})
        subm_count_mock.assert_called_once_with(self.auth_user, expected_since_date)

    def test_monthly_counts_thirty_days_from_now(self, subm_count_mock, dt_now):
        dt_now.return_value = self.now_date
        subm_count_mock.return_value = {'x': 'x'}
        expected_since_date = self.now_date - timedelta(days=30)
        response = self.client.get(f'/accounts/user/{self.auth_user.id}/recent_submissions?date_mode=monthly',
                                   HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'x': 'x'})
        subm_count_mock.assert_called_once_with(self.auth_user, expected_since_date)

    def test_yearly_counts_365_days_from_now(self, subm_count_mock, dt_now):
        dt_now.return_value = self.now_date
        subm_count_mock.return_value = {'x': 'x'}
        expected_since_date = self.now_date - timedelta(days=365)
        response = self.client.get(f'/accounts/user/{self.auth_user.id}/recent_submissions?date_mode=yearly',
                                   HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'x': 'x'})
        subm_count_mock.assert_called_once_with(self.auth_user, expected_since_date)

    def test_no_date_mode_returns_400(self, subm_count_mock, _):
        response = self.client.get(f'/accounts/user/{self.auth_user.id}/recent_submissions',
                                   HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)
        subm_count_mock.assert_not_called()

    def test_invalid_date_mode_returns_400(self, subm_count_mock, _):
        response = self.client.get(f'/accounts/user/{self.auth_user.id}/recent_submissions?date_mode=tank',
                                   HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)
        subm_count_mock.assert_not_called()

    def test_invalid_user_returns_404(self, subm_count_mock, _):
        response = self.client.get(f'/accounts/user/111/recent_submissions', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 404)
        subm_count_mock.assert_not_called()

    def test_requires_authentication(self, subm_count_mock, _):
        response = self.client.get(f'/accounts/user/{self.auth_user.id}/recent_submissions')

        self.assertEqual(response.status_code, 401)
        subm_count_mock.assert_not_called()
