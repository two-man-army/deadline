""" Tests associated with the Challenge model and views """
from unittest import skip

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
