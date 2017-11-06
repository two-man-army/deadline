from rest_framework.test import APITestCase

from accounts.models import User, Role


class LeaderboardViewTest(APITestCase):
    def setUp(self):
        """
        Create users with expected positions
        """
        self.role = Role.objects.create(name='Basic')
        self.first_user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.role)
        self.second_user = User.objects.create(username='dGuy', email='d@abv.dg', password='123', score=122, role=self.role)
        self.second_user2 = User.objects.create(username='dGumasky', email='molly@abv.bg', password='123', score=122, role=self.role)
        self.second_user3 = User.objects.create(username='xdGumasky', email='xmolly@abv.bg', password='123', score=122, role=self.role)
        self.fifth_user = User.objects.create(username='dbrr', email='dd@abv.bg', password='123', score=121, role=self.role)

    def test_view_returns_expected_position(self):
        auth_token = 'Token {}'.format(self.first_user.auth_token.key)
        received_data = self.client.get('/challenges/selfLeaderboardPosition', HTTP_AUTHORIZATION=auth_token).data
        self.assertEqual(received_data['position'], 1)
        self.assertEqual(received_data['leaderboard_count'], 5)

    def test_view_returns_expected_last_position(self):
        auth_token = 'Token {}'.format(self.fifth_user.auth_token.key)
        received_data = self.client.get('/challenges/selfLeaderboardPosition', HTTP_AUTHORIZATION=auth_token).data

        self.assertEqual(received_data['position'], 5)
        self.assertEqual(received_data['leaderboard_count'], 5)

    def test_view_returns_expected_multiple_user_position(self):
        """ When multiple users have the same score and position, should return that position """
        auth_token = 'Token {}'.format(self.second_user3.auth_token.key)
        received_data = self.client.get('/challenges/selfLeaderboardPosition', HTTP_AUTHORIZATION=auth_token).data

        self.assertEqual(received_data['position'], 2)
        self.assertEqual(received_data['leaderboard_count'], 5)

    def test_get_leaderboard(self):
        """
        Should return a leaderboard with each user's position
        we expect each second_user* to be at 2nd place and the fifth user to be at fifth
        """
        expected_positions = {
            self.fifth_user.username: 5,
            self.second_user.username: 2,
            self.second_user2.username: 2,
            self.second_user3.username: 2,
            self.first_user.username: 1
        }
        auth_token = 'Token {}'.format(self.second_user3.auth_token.key)

        received_leaderboard = self.client.get('/challenges/getLeaderboard', HTTP_AUTHORIZATION=auth_token).data

        for lead in received_leaderboard:
            user_name = lead['name']
            self.assertEqual(lead['position'], expected_positions[user_name])
