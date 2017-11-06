from rest_framework.test import APITestCase

from accounts.models import User, Role


class UserDetailsViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        self.auth_token = 'Token {}'.format(self.user.auth_token.key)

    def test_returns_expected_data(self):
        response = self.client.get(f'/accounts/user/{self.user.id}/', HTTP_AUTHORIZATION=self.auth_token)
        expected_data = {'id': self.user.id, 'username': self.user.username, 'email': self.user.email,
                 'score': self.user.score,
                 'follower_count': self.user.followers.count(),
                 'role': {'id': self.user.role.id, 'name': self.user.role.name}}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_requires_authentication(self):
        response = self.client.get(f'/accounts/user/{self.user.id}/')
        self.assertEqual(response.status_code, 401)
