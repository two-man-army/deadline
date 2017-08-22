from rest_framework.test import APITestCase

from accounts.models import User, Role
from social.models import Notification


class UserFollowViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.first_user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123,
                                              role=self.base_role)
        self.first_user_auth_token = 'Token {}'.format(self.first_user.auth_token.key)
        self.second_user = User.objects.create(username='dGuy', email='d@abv.dg', password='123', score=122,
                                               role=self.base_role)
        self.second_user_auth_token = 'Token {}'.format(self.second_user.auth_token.key)

    def test_follows(self):
        response = self.client.post(f'/social/follow?target={self.second_user.id}', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.second_user.followers.count(), 1)
        self.assertEqual(self.first_user.users_followed.count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.second_user).count(), 1)

    def test_cannot_follow_same_person_twice(self):
        self.client.post(f'/social/follow?target={self.second_user.id}', HTTP_AUTHORIZATION=self.first_user_auth_token)
        second_response = self.client.post(f'/social/follow?target={self.second_user.id}', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(self.second_user.followers.count(), 1)
        self.assertEqual(self.first_user.users_followed.count(), 1)

    def test_returns_400_if_invalid_querystring(self):
        response = self.client.post(f'/social/follow?target=NINTENDO', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_querystring_missing(self):
        response = self.client.post(f'/social/follow', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 400)

    def test_returns_404_if_invalid_user(self):
        response = self.client.post(f'/social/follow?target=111', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 404)

    def test_requires_authentication(self):
        response = self.client.post(f'/social/follow?target={self.second_user.id}')
        self.assertEqual(response.status_code, 401)


class UserUnfollowViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.first_user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123,
                                              role=self.base_role)
        self.first_user_auth_token = 'Token {}'.format(self.first_user.auth_token.key)
        self.second_user = User.objects.create(username='dGuy', email='d@abv.dg', password='123', score=122,
                                               role=self.base_role)
        self.second_user_auth_token = 'Token {}'.format(self.second_user.auth_token.key)

    def test_follows(self):
        self.first_user.follow(self.second_user)
        response = self.client.post(f'/social/unfollow?target={self.second_user.id}', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.second_user.followers.count(), 0)
        self.assertEqual(self.first_user.users_followed.count(), 0)

    def test_cannot_unfollow_user_that_is_not_followed(self):
        response = self.client.post(f'/social/unfollow?target={self.second_user.id}', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.second_user.followers.count(), 0)
        self.assertEqual(self.first_user.users_followed.count(), 0)

    def test_returns_400_if_invalid_querystring(self):
        response = self.client.post(f'/social/unfollow?target=NINTENDO', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_querystring_missing(self):
        response = self.client.post(f'/social/unfollow', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 400)

    def test_returns_404_if_invalid_user(self):
        response = self.client.post(f'/social/unfollow?target=111', HTTP_AUTHORIZATION=self.first_user_auth_token)
        self.assertEqual(response.status_code, 404)

    def test_returns_401_if_unauth(self):
        response = self.client.post(f'/social/unfollow?target={self.second_user.id}')
        self.assertEqual(response.status_code, 401)
