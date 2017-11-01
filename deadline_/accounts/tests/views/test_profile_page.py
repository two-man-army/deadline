from rest_framework.test import APITestCase

from accounts.models import User, Role, UserPersonalDetails
from accounts.serializers import UserPersonalDetailsSerializer
from challenges.tests.factories import UserFactory, UserPersonalDetailsFactory


class ProfilePageInfoViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123,
                                        role=self.base_role)
        self.profile_user = User.objects.create(username='Ben Foster', email='ben@abv.bg', password='123', score=123,
                                                role=self.base_role)
        UserPersonalDetailsFactory(user=self.profile_user)
        # create two followers
        UserFactory().follow(self.profile_user)
        UserFactory().follow(self.profile_user)
        self.user.follow(self.profile_user)
        self.profile_user.follow(self.user)
        self.auth_token = 'Token {}'.format(self.user.auth_token.key)

    def test_returns_expected_data(self):
        expected_data = {
            'following': True,  # auth user is following him
            'following_count': self.profile_user.users_followed.count(),
            'followers_count': self.profile_user.followers.count(),
            'registered_on': self.profile_user.created_at.isoformat(),
            "user_details": UserPersonalDetailsSerializer(instance=self.profile_user.personal_details).data
        }

        response = self.client.get(f'/accounts/user/{self.profile_user.id}/profile', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_returns_404_on_invalid_user_id(self):
        response = self.client.get(f'/accounts/user/123/profile', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_returns_401_when_unauthenticated(self):
        response = self.client.get(f'/accounts/user/{self.profile_user.id}/profile')
        self.assertEqual(response.status_code, 401)
