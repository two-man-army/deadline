import re
from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock

import jwt
from django.http import HttpResponse
from django.test import TestCase
from django.utils.six import BytesIO
from rest_framework.test import APITestCase
from rest_framework.parsers import JSONParser

from accounts.constants import (
    NOTIFICATION_SECRET_KEY, FACEBOOK_PROFILE_REGEX, TWITTER_PROFILE_REGEX,
    GITHUB_PROFILE_REGEX, LINKEDIN_PROFILE_REGEX
)
from accounts.errors import UserAlreadyFollowedError, UserNotFollowedError
from accounts.helpers import generate_notification_token
from accounts.models import User, Role, UserPersonalDetails
from accounts.serializers import UserSerializer
from challenges.tests.factories import UserFactory, ChallengeDescFactory
from challenges.models import (Challenge, Submission, Language, SubmissionVote, Proficiency,
                               UserSubcategoryProficiency, SubCategory, MainCategory)
from social.constants import NW_ITEM_TEXT_POST
from social.models.newsfeed_item import NewsfeedItem
from social.models.notification import Notification


class RegisterViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')

    def test_register(self):
        # The user posts his username, email and password to the /accounts/register URL
        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'meredith@abv.bg'})
        # Should have successfully register the user and gave him a user token
        self.assertEqual(response.status_code, 201)
        self.assertTrue('user_token' in response.data)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserPersonalDetails.objects.count(), 1)

    def test_register_existing_user_should_return_400(self):
        User.objects.create(email='that_part@abv.bg', password='123', username='ThatPart', role=self.base_role)

        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'that_part@abv.bg'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertIn('email already exists', ''.join(response.data['email']))

    def test_register_existing_username_should_return_400(self):
        User.objects.create(email='that_part@abv.bg', password='123', username='ThatPart', role=self.base_role)

        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'ThatPart',
                                                                               'password': 'mer19222',
                                                                               'email': 'TANKTNAK@abv.bg'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data)
        self.assertIn('username already exists', ''.join(response.data['username']))
