""" Tests associated with the Challenge model and views """
from unittest import skip

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


# TODO: Add supported languages to tests
class ChallengesModelTest(TestCase):
    def setUp(self):
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.sample_desc = ChallengeDescFactory()
        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)

    def test_absolute_url(self):
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        expected_url = '/challenges/{}'.format(c.id)
        self.assertEqual(c.get_absolute_url(), expected_url)

    def test_can_create_comment(self):
        self.base_role = Role.objects.create(name='User')
        self.main_cat = MainCategory.objects.create(name='tank')
        self.starter_proficiency = Proficiency.objects.create(name="scrub", needed_percentage=0)
        us = UserFactory()
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        comment = c.add_comment(author=us, content='Hello, how are you :)')

        self.assertEqual(c.comments.count(), 1)
        self.assertEqual(c.comments.first(), comment)
        self.assertEqual(comment.author, us)
        self.assertEqual(comment.content, 'Hello, how are you :)')
        self.assertIsNotNone(comment.created_at)

    def test_cannot_save_duplicate_challenge(self):
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
            c.full_clean()

    def test_cannot_have_three_digit_or_invalid_difficulty(self):
        test_difficulties = [1.11, 1.111, 1.55, 1.4999]  # should all raise
        for diff in test_difficulties:
            sample_desc = ChallengeDescFactory(); sample_desc.save()

            c = Challenge.objects.create(name='Hello'+str(diff), difficulty=diff, score=10, test_case_count=5, category=self.sub_cat,
                          description=sample_desc, test_file_name='tank')

            with self.assertRaises(ValidationError):
                c.full_clean()

        sample_desc = ChallengeDescFactory(); sample_desc.save()
        c = Challenge.objects.create(name='Hello For The Last Time', difficulty=1.5, score=10, test_case_count=5,
                                     category=self.sub_cat,
                                     description=sample_desc, test_file_name='tank')
        c.full_clean()  # should not raise

    def test_cannot_have_duplicate_descriptions(self):
        c = Challenge(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat,
                      description=self.sample_desc)
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge(name='Working', difficulty=5, score=10, test_case_count=1, category=self.sub_cat,
                          description=self.sample_desc)
            c.full_clean()

    def test_cannot_have_same_language_twice(self):
        lang_1 = Language.objects.create(name="AA")
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat,
                      description=self.sample_desc)
        c.supported_languages.add(lang_1)
        c.save()
        c.supported_languages.add(lang_1)
        c.save()
        self.assertEqual(c.supported_languages.count(), 1)

    def test_cannot_save_blank_challenge(self):
        c = Challenge()
        with self.assertRaises(Exception):
            c.full_clean()

    @skip
    def test_deserialization(self):
        self.fail("Implement deserialization somewhere down the line, with the ability to create a description object from the challenge serialization. You're gonna need to override the serializer's create method")
        expected_json = b'{"name":"Hello","difficulty":5.0,"score":10,"description":"' + str(None) + '","test_case_count":3,"category":"tests"}'
        data = JSONParser().parse(BytesIO(expected_json))
        serializer = ChallengeSerializer(data=data)
        serializer.is_valid()

        deser_challenge = serializer.save()
        self.assertEqual(deser_challenge.name, "Hello")
        self.assertEqual(deser_challenge.difficulty, 5)
        self.assertEqual(deser_challenge.score, 10)
        self.assertEqual(deser_challenge.description, "What up")

    def test_invalid_deserialization(self):
        # No name!
        expected_json = b'{"difficulty":5.0, "score":10, "description":"What up"}'
        data = JSONParser().parse(BytesIO(expected_json))
        serializer = ChallengeSerializer(data=data)

        self.assertFalse(serializer.is_valid())


class ChallengesDescriptionModelTest(TestCase):
    def setUp(self):
        self.description = ChallengeDescFactory()

    def test_serialization(self):
        expected_json = f'{{"content":"{self.description.content}","input_format":"{self.description.input_format}",' \
                        f'"output_format":"{self.description.output_format}","constraints":"{self.description.constraints}",' \
                        f'"sample_input":"{self.description.sample_input}","sample_output":"{self.description.sample_output}",' \
                        f'"explanation":"{self.description.explanation}"}}'
        received_data = JSONRenderer().render(ChallengeDescriptionSerializer(self.description).data)

        self.assertEqual(received_data.decode('utf-8').replace('\\', ''), expected_json)


class ChallengesViewsTest(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

        self.sample_desc = ChallengeDescFactory()
        self.rust_lang = Language.objects.create(name='Rust')
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        self.c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_file_name='hello_test.py',
                                     test_case_count=2, category=self.sub_cat, description=self.sample_desc)
        self.c.supported_languages.add(self.rust_lang)

    def test_view_challenge(self):
        response = self.client.get(f'/challenges/{self.c.id}', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChallengeSerializer(self.c).data, response.data)

    def test_view_challenge_doesnt_exist(self):
        response = self.client.get('/challenges/3', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_challenge_unauthorized_should_return_401(self):

        response = self.client.get(f'/challenges/{self.c.id}')

        self.assertEqual(response.status_code, 401)


class ChallengeCommentViewTest(APITestCase, TestHelperMixin):
    def setUp(self):
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.python_language = Language.objects.create(name="Python")

        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.c1 = ChallengeFactory(category=self.sub_cat)
        self.create_user_and_auth_token()

    # Comment Create Tests
    def test_create_comment(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.c1.comments.count(), 1)
        self.assertEqual(self.c1.comments.first().author, self.auth_user)
        self.assertEqual(self.c1.comments.first().content, 'Hello World')

    def test_returns_400_if_comment_is_not_str(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 123456}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_comment_is_too_short(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'wh'})
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_comment_is_too_long(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'*500})
        self.assertEqual(response.status_code, 400)

    def test_non_existent_challenge_returns_404(self):
        response = self.client.post(f'/challenges/111/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})
        self.assertEqual(response.status_code, 404)

    def test_requires_authentication(self):
        response = self.client.post(f'/challenges/111/comments',
                                    data={'content': 'Hello World'})
        self.assertEqual(response.status_code, 401)

        # Comment Create Tests
