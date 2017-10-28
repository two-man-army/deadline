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


class HelpersTest(TestCase):
    @patch('accounts.helpers.NOTIFICATION_TOKEN_EXPIRY_MINUTES', 20)
    @patch('accounts.helpers.jwt.encode')
    @patch('accounts.helpers.get_utc_time')
    def test_generate_notification_token(self, mock_utc_time, mock_jwt_encode):
        utc_time = datetime.utcnow()
        mock_utc_time.return_value = utc_time
        expected_expiry_date = utc_time + timedelta(minutes=20)
        mock_jwt_encode.return_value = MagicMock(decode=lambda x: 'chrissy')

        notif_token = generate_notification_token(MagicMock(username='yo'))

        mock_jwt_encode.assert_called_once_with({'exp': expected_expiry_date, 'username': 'yo'}, NOTIFICATION_SECRET_KEY)
        self.assertEqual('chrissy', notif_token)


class RegexesTest(TestCase):
    def assertMatchesURL(self, match_regex, url):
        self.assertIsNotNone(re.match(match_regex, url),
                             msg=f'{url} did not match regex {match_regex}!')

    def assertDoesNotMatchURL(self, match_regex, url):
        self.assertIsNone(re.match(match_regex, url),
                          msg=f'{url} matched {match_regex}!')

    def test_facebook_profile_regex_matches_positives(self):
        valid_links = [
            'http://www.facebook.com/mypageusername?ref=hl',
            'facebook.com/mypageusername',
            'https://www.facebook.com/yourworldwithin/?hc_ref=ARTWAkSewGoStjGHFn1spDJc7YNtPHH570Ep9i5-FiVsGwcOH-Vqoz3tE8xZpEnXXlE&fref=nf'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(FACEBOOK_PROFILE_REGEX, valid_link)

    def test_facebook_profile_regex_matches_page_name(self):
        profile_name_by_link = {
            'http://www.facebook.com/mypageusername?ref=hl': 'mypageusername',
            'facebook.com/mypageusername': 'mypageusername',
            'https://www.facebook.com/yourworldwithin/?hc_ref=ARTWAkSewGoStjGHFn1spDJc7YNtPHH570Ep9i5-FiVsGwcOH-Vqoz3tE8xZpEnXXlE&fref=nf': 'yourworldwithin'
        }
        for link, profile_name in profile_name_by_link.items():
            extracted_page_name = re.match(FACEBOOK_PROFILE_REGEX, link).group('page_name')
            self.assertEqual(extracted_page_name, profile_name)

    def test_facebook_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'http://www.fасеbook.com/mypageusername',  # cyrillic characters in URL
            'https://www.facebook.co/mypageusername?ref=hl',
            'http://www.facebook.org/pages/Vanity-Url/12345678?ref=hl',
            'https://www.fb-page.com/pages/Vanity-Url/12345678?ref=hl',
            'https://www.facebook.com/heymelikey/photos/a.760078844002883.1073741828.759042127439888/1742633762414048/?type=3',
            'https://www.facebook.com/hnbot/posts/1514015915320351'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(FACEBOOK_PROFILE_REGEX, invalid_link)

    def test_twitter_profile_regex_matches_positives(self):
        valid_links = [
            'https://twitter.com/barackobama?lang=bgdDdas214913r_#qrfcDJAMBOXs\\\\\\\d',
            'https://twitter.com/EdubHipHop',
            'twitter.com/EdubHipHop?lang=bg'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(TWITTER_PROFILE_REGEX, valid_link)

    def test_twitter_profile_regex_matches_profile_name(self):
        profile_name_by_link = {
            'https://twitter.com/barackobama?lang=bgdDdas214913r_#qrfcDJAMBOXs\\\\\\\d': 'barackobama',
            'https://twitter.com/EdubHipHop': 'EdubHipHop',
            'twitter.com/EdubHipHop?lang=bg': 'EdubHipHop'
        }
        for link, profile_name in profile_name_by_link.items():
            extracted_page_name = re.match(TWITTER_PROFILE_REGEX, link).group('profile_name')
            self.assertEqual(extracted_page_name, profile_name)

    def test_twitter_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'https://twittеr.соm/EdubHipHop',  # cyrillic
            'twitter.co/EdubHipHop?lang=bg'
            'https://twtr.com/EdubHipHop?lang=bg'
            'https://twitter.com/EdubHipHop/status/761547917882695681'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(TWITTER_PROFILE_REGEX, invalid_link)

    def test_github_profile_regex_matches_positives(self):
        valid_links = [
            'www.github.com/Enether',
            'www.github.com/vgramov?te=334'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(GITHUB_PROFILE_REGEX, valid_link)

    def test_github_profile_regex_matches_profile_name(self):
        usernames_by_links = {
            'www.github.com/Enether': 'Enether',
            'www.github.com/vgramov?te=334': 'vgramov'
        }
        for link, username in usernames_by_links.items():
            extracted_page_name = re.match(GITHUB_PROFILE_REGEX, link).group('profile_name')
            self.assertEqual(extracted_page_name, username)

    def test_github_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'www.github.соm/Enether',  # cyrillic
            'www.github.co/vgramov?te=334'
            'www.github.com/vgramov/java_game'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(GITHUB_PROFILE_REGEX, invalid_link)

    def test_linkedin_profile_regex_matches_positives(self):
        valid_links = [
            'https://www.linkedin.com/in/williamhgates/',
            'www.linkedin.com/in/stanislavkozlovski?lang=bg',
            'www.linkedin.com/in/tank-mihailov-a52a1498/'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(LINKEDIN_PROFILE_REGEX, valid_link)

    def test_linkedin_profile_regex_matches_profile_name(self):
        usernames_by_links = {
            'https://www.linkedin.com/in/williamhgates/': 'williamhgates',
            'www.linkedin.com/in/stanislavkozlovski?lang=bg': 'stanislavkozlovski',
            'www.linkedin.com/in/tank-mihailov-a52a1498/': 'tank-mihailov-a52a1498'
        }
        for link, username in usernames_by_links.items():
            extracted_page_name = re.match(LINKEDIN_PROFILE_REGEX, link).group('profile_name')
            self.assertEqual(extracted_page_name, username)

    def test_linkedin_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'https://www.linkedin.com/company/deadline/',
            'www.linkedin.com/in//'
            'www.linkedin.com/tank-mihailov-a52a1498/'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(LINKEDIN_PROFILE_REGEX, invalid_link)
