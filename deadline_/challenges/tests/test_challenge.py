""" Tests associated with the Challenge model and views """
from unittest import skip
from unittest.mock import patch, MagicMock, ANY

from django.db import IntegrityError
from django.test import TestCase
from django.utils.six import BytesIO
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from challenges.models import Challenge, MainCategory, SubCategory, ChallengeDescription, Language, Proficiency
from challenges.serializers import ChallengeSerializer, ChallengeDescriptionSerializer
from challenges.tests.factories import ChallengeDescFactory, UserFactory, ChallengeFactory
from challenges.tests.base import TestHelperMixin
from accounts.models import User, Role


class ChallengesModelTest(TestCase):
    def setUp(self):
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.sample_desc = ChallengeDescFactory()
        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)

    def test_absolute_url(self):
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        expected_url = '/challenges/{}'.format(c.id)
        self.assertEqual(c.get_absolute_url(), expected_url)

    def test_cannot_save_duplicate_challenge(self):
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
            c.full_clean()

    def test_cannot_have_three_digit_or_invalid_difficulty(self):
        test_difficulties = [1.11, 1.111, 1.55, 1.4999]  # should all raise
        for diff in test_difficulties:
            with self.assertRaises(ValidationError):
                ChallengeFactory(difficulty=diff).full_clean()

    def test_cannot_have_duplicate_descriptions(self):
        desc = ChallengeDescFactory()
        ChallengeFactory(description=desc)
        with self.assertRaises(IntegrityError):
            ChallengeFactory(description=desc)

    def test_cannot_have_same_language_twice(self):
        lang_1 = Language.objects.create(name="AA")
        c = ChallengeFactory()
        c.supported_languages.add(lang_1)
        c.save()
        c.supported_languages.add(lang_1)
        c.save()
        self.assertEqual(c.supported_languages.count(), 1)

    def test_cannot_save_blank_challenge(self):
        c = Challenge()
        with self.assertRaises(Exception):
            c.full_clean()

    def test_fetch_five_latest_challenges(self):
        # create 10 challenges
        expected_latest_five = []
        for i in range(10):
            c = Challenge.objects.create(name=f'Hello{i}', difficulty=5, score=10, test_case_count=5, category=self.sub_cat,
                                         description=ChallengeDescFactory())
            if i >= 5:  # last five should be the latest
                expected_latest_five.append(c)
        expected_latest_five = list(reversed(expected_latest_five))  # first challenge must be first

        latest_five = Challenge.objects.fetch_five_latest_challenges_by_page(page=1)

        self.assertEqual(expected_latest_five, latest_five)

    def test_fetch_five_latest_challenges_works_with_string_number_passed(self):
        # create 10 challenges
        expected_latest_five = []
        for i in range(10):
            c = Challenge.objects.create(name=f'Hello{i}', difficulty=5, score=10, test_case_count=5,
                                         category=self.sub_cat,
                                         description=ChallengeDescFactory())
            if i >= 5:  # last five should be the latest
                expected_latest_five.append(c)
        expected_latest_five = list(reversed(expected_latest_five))  # first challenge must be first

        latest_five = Challenge.objects.fetch_five_latest_challenges_by_page(page='1')

        self.assertEqual(expected_latest_five, latest_five)

    def test_fetch_five_latest_challenges_second_page(self):
        # create 8 challenges
        expected_oldest_three = []
        for i in range(8):
            c = Challenge.objects.create(name=f'Hello{i}', difficulty=5, score=10, test_case_count=5,
                                         category=self.sub_cat,
                                         description=ChallengeDescFactory())
            if i < 3:  # first three should be in the oldest page
                expected_oldest_three.append(c)
        expected_oldest_three = list(reversed(expected_oldest_three))  # latest challenge must be first

        received_three = Challenge.objects.fetch_five_latest_challenges_by_page(page=2)

        self.assertEqual(len(received_three), 3)
        self.assertEqual(expected_oldest_three, received_three)

    def test_fetch_five_latest_challenges_invalid_page(self):
        for i in range(8):
            Challenge.objects.create(name=f'Hello{i}', difficulty=5, score=10,
                                     test_case_count=5, category=self.sub_cat, description=ChallengeDescFactory())
        self.assertEqual(Challenge.objects.fetch_five_latest_challenges_by_page(page=3), [])
        self.assertEqual(Challenge.objects.fetch_five_latest_challenges_by_page(page=-1), [])
        self.assertEqual(Challenge.objects.fetch_five_latest_challenges_by_page(page=None), [])


class ChallengesDescriptionModelTest(TestCase):
    def setUp(self):
        self.d: ChallengeDescription = ChallengeDescFactory()

    def test_serialization(self):
        expected_data = {
            'content': self.d.content, 'input_format': self.d.input_format, 'output_format': self.d.output_format,
            'constraints': self.d.constraints, 'sample_input': self.d.sample_input,
            'sample_output': self.d.sample_output, 'explanation': self.d.explanation
        }
        received_data = ChallengeDescriptionSerializer(self.d).data

        self.assertEqual(received_data, expected_data)


class ChallengesViewsTest(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    def test_view_challenge(self):
        response = self.client.get(f'/challenges/{self.challenge.id}', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChallengeSerializer(self.challenge).data, response.data)

    def test_view_challenge_doesnt_exist_should_return_404(self):
        response = self.client.get('/challenges/3', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_challenge_unauthorized_should_return_401(self):
        response = self.client.get(f'/challenges/{self.challenge.id}')
        self.assertEqual(response.status_code, 401)

    @patch('challenges.views.Challenge.objects.fetch_five_latest_challenges_by_page')
    @patch('challenges.views.LimitedChallengeSerializer')
    def test_view_latest_challenges(self, mock_serializer, mock_fetch):
        """
        Should returns the latest 5 challenges
        """
        mock_fetch.return_value = 'chals'
        mock_serializer.return_value = MagicMock(data='tank')
        resp = self.client.get('/challenges/latest?page=1', HTTP_AUTHORIZATION=self.auth_token)

        mock_fetch.assert_called_once_with(page='1')
        mock_serializer.assert_called_once_with(mock_fetch.return_value, many=True, context={'request': ANY})
        self.assertEqual(resp.data, mock_serializer().data)
        self.assertEqual(resp.status_code, 200)

    def test_view_latest_challenges_requires_auth(self):
        resp = self.client.get('/challenges/latest?page=1')
        self.assertEqual(resp.status_code, 401)
