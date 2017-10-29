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
from accounts.serializers import UserSerializer, UserPersonalDetailsSerializer
from challenges.tests.factories import UserFactory, ChallengeDescFactory
from challenges.models import (Challenge, Submission, Language, SubmissionVote, Proficiency,
                               UserSubcategoryProficiency, SubCategory, MainCategory)
from social.constants import NW_ITEM_TEXT_POST
from social.models.newsfeed_item import NewsfeedItem
from social.models.notification import Notification


class UserPersonalDetailsSerializerTest(TestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.main_user = User.objects.create(username='main_user', password='123', email='main_user@abv.bg', score=123,
                                             role=self.base_role)
        self.personal_details = UserPersonalDetails.objects.create(user=self.main_user, interests=[])

    def assertSerializerContainsErrorForField(self, serializer, field):
        self.assertIn(field, serializer.errors)

    def test_parses_input_and_saves_as_expected(self):
        user_data = {
            'about': 'Become the best you can possibly be',
            'country': 'Spain',
            'city': 'Madrid',
            'job_title': 'DevOps',
            'job_company': 'Facebook',
            'personal_website': 'https://www.me.com',
            'interests': ['Skiing', 'Hiking', 'Coffee', 'Mountain Climbing'],
            'facebook_profile': 'facebook.com/mypageusername',
            'twitter_profile': 'https://twitter.com/EdubHipHop',
            'github_profile': 'www.github.com/vgramov?te=334'
        }

        serializer = UserPersonalDetailsSerializer(self.personal_details, data=user_data, partial=True)
        is_valid = serializer.is_valid()
        self.assertTrue(is_valid, msg=f'Invalid Data: {serializer.errors}')
        serializer.save()
        self.personal_details.refresh_from_db()

        self.assertEqual(self.personal_details.linkedin_profile, '')
        self.assertEqual(self.personal_details.github_profile, 'vgramov')
        self.assertEqual(self.personal_details.twitter_profile, 'EdubHipHop')
        self.assertEqual(self.personal_details.facebook_profile, 'mypageusername')
        self.assertEqual(self.personal_details.interests, ['Skiing', 'Hiking', 'Coffee', 'Mountain Climbing'])
        self.assertEqual(self.personal_details.personal_website, 'https://www.me.com')
        self.assertEqual(self.personal_details.job_title, 'DevOps')
        self.assertEqual(self.personal_details.job_company, 'Facebook')
        self.assertEqual(self.personal_details.about, 'Become the best you can possibly be')
        self.assertEqual(self.personal_details.country, 'Spain')
        self.assertEqual(self.personal_details.city, 'Madrid')

    def test_returns_error_on_invalid_website_link(self):
        serializer = UserPersonalDetailsSerializer(self.personal_details,
                                                   data={'personal_website': 'hitemup'},
                                                   partial=True)
        is_valid = serializer.is_valid()
        self.personal_details.refresh_from_db()

        self.assertFalse(is_valid)
        self.assertSerializerContainsErrorForField(serializer, 'personal_website')

    def test_returns_error_on_invalid_twitter_profile(self):
        serializer = UserPersonalDetailsSerializer(self.personal_details,
                                                   data={'twitter_profile': 'www.linkedin.com/in/wtf'},
                                                   partial=True)
        is_valid = serializer.is_valid()
        self.personal_details.refresh_from_db()

        self.assertFalse(is_valid)
        self.assertSerializerContainsErrorForField(serializer, 'twitter_profile')

    def test_returns_error_on_invalid_facebook_profile(self):
        serializer = UserPersonalDetailsSerializer(self.personal_details,
                                                   data={'facebook_profile': 'www.fffb.com/wtf'},
                                                   partial=True)
        is_valid = serializer.is_valid()
        self.personal_details.refresh_from_db()

        self.assertFalse(is_valid)
        self.assertSerializerContainsErrorForField(serializer, 'facebook_profile')

    def test_returns_error_on_invalid_github_profile(self):
        serializer = UserPersonalDetailsSerializer(self.personal_details,
                                                   data={'github_profile': 'UP:)'},
                                                   partial=True)
        is_valid = serializer.is_valid()
        self.personal_details.refresh_from_db()

        self.assertFalse(is_valid)
        self.assertSerializerContainsErrorForField(serializer, 'github_profile')

    def test_returns_error_on_invalid_linkedin_profile(self):
        self.personal_details.linkedin_profile = 'Enether'
        self.personal_details.save()
        serializer = UserPersonalDetailsSerializer(self.personal_details,
                                                   data={'linkedin_profile': 'www.dir.bg/UP'},
                                                   partial=True)
        is_valid = serializer.is_valid()
        self.personal_details.refresh_from_db()

        self.assertFalse(is_valid)
        self.assertSerializerContainsErrorForField(serializer, 'linkedin_profile')

    def test_returns_error_on_too_many_interests(self):
        interests = [
            'gangster rap', 'coffee', 'mountain climb', 'pills', 'rapping',
            'driving'
        ]
        serializer = UserPersonalDetailsSerializer(self.personal_details,
                                                   data={'interests': interests},
                                                   partial=True)
        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertSerializerContainsErrorForField(serializer, 'interests')
