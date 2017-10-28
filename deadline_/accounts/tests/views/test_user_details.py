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


class UserDetailsViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        self.auth_token = 'Token {}'.format(self.user.auth_token.key)

    def test_returns_expected_data(self):
        response = self.client.get(f'/accounts/user/{self.user.id}', HTTP_AUTHORIZATION=self.auth_token)
        expected_data = {'id': self.user.id, 'username': self.user.username, 'email': self.user.email,
                 'score': self.user.score,
                 'follower_count': self.user.followers.count(),
                 'role': {'id': self.user.role.id, 'name': self.user.role.name}}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_requires_authentication(self):
        response = self.client.get(f'/accounts/user/{self.user.id}')
        self.assertEqual(response.status_code, 401)
