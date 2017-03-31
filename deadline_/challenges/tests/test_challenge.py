""" Tests associated with the Challenge model and views """
from unittest import skip

from django.test import TestCase
from django.utils.six import BytesIO
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from challenges.models import Challenge, MainCategory, SubCategory, ChallengeDescription, Language
from challenges.serializers import ChallengeSerializer, ChallengeDescriptionSerializer
from accounts.models import User

# TODO: Add supported languages to tests
class ChallengesModelTest(TestCase):
    def setUp(self):
        challenge_cat = MainCategory('Tests')
        challenge_cat.save()
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')

        self.sample_desc.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()

    def test_absolute_url(self):
        c = Challenge(name='Hello', rating=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        expected_url = '/challenges/{}'.format(c.id)
        self.assertEqual(c.get_absolute_url(), expected_url)

    def test_cannot_save_duplicate_challenge(self):
        c = Challenge(name='Hello', rating=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge(name='Hello', rating=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
            c.full_clean()

    def test_cannot_have_duplicate_descriptions(self):
        c = Challenge(name='Hello', rating=5, score=10, test_case_count=5, category=self.sub_cat,
                      description=self.sample_desc)
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge(name='Working', rating=5, score=10, test_case_count=1, category=self.sub_cat,
                          description=self.sample_desc)
            c.full_clean()

    def test_cannot_have_same_language_twice(self):
        lang_1 = Language(name="AA")
        lang_1.save()
        c = Challenge(name='Hello', rating=5, score=10, test_case_count=5, category=self.sub_cat,
                      description=self.sample_desc)
        c.save()
        c.supported_languages.add(lang_1)
        c.supported_languages.add(lang_1)
        c.save()
        self.assertEqual(len(c.supported_languages.all()), 1)

    def test_cannot_save_blank_challenge(self):
        c = Challenge()
        with self.assertRaises(Exception):
            c.full_clean()

    def test_serialization(self):
        rust_lang = Language('Rust'); rust_lang.save()
        python_lang = Language('Python'); python_lang.save()
        c_lang = Language('C'); c_lang.save()
        c = Challenge(name='Hello', rating=5, score=10, test_case_count=5, category=self.sub_cat, description=self.sample_desc)
        c.save()
        c.supported_languages.add(*[rust_lang, c_lang, python_lang])
        expected_description_json = '{"content":"What Up","input_format":"Something",' \
                                    '"output_format":"something","constraints":"some",' \
                                    '"sample_input":"input sample","sample_output":"output sample",' \
                                    '"explanation":"gotta push it to the limit"}'
        expected_json = ('{"id":1,"name":"Hello","rating":5,"score":10,"description":'
                         + expected_description_json
                         + ',"test_case_count":5,"category":"tests","supported_languages":["C","Python","Rust"]}')
        self.maxDiff = None
        content = JSONRenderer().render(ChallengeSerializer(c).data)
        self.assertEqual(content.decode('utf-8'), expected_json)

    @skip
    def test_deserialization(self):
        self.fail("Implement deserialization somewhere down the line, with the ability to create a description object from the challenge serialization. You're gonna need to override the serializer's create method")
        expected_json = b'{"name":"Hello","rating":5,"score":10,"description":"' + str(None) + '","test_case_count":3,"category":"tests"}'
        data = JSONParser().parse(BytesIO(expected_json))
        serializer = ChallengeSerializer(data=data)
        serializer.is_valid()

        deser_challenge = serializer.save()
        self.assertEqual(deser_challenge.name, "Hello")
        self.assertEqual(deser_challenge.rating, 5)
        self.assertEqual(deser_challenge.score, 10)
        self.assertEqual(deser_challenge.description, "What up")

    def test_invalid_deserialization(self):
        # No name!
        expected_json = b'{"rating":5, "score":10, "description":"What up"}'
        data = JSONParser().parse(BytesIO(expected_json))
        serializer = ChallengeSerializer(data=data)

        self.assertFalse(serializer.is_valid())


class ChallengesDescriptionModelTest(TestCase):
    def setUp(self):
        self.description = ChallengeDescription(
            content='You need to print out Hello World!',
            input_format='',
            output_format='The word "Hello World!" in a single line',
            constraints='Time: 10s',
            sample_input='',
            sample_output='Hello World!',
            explanation='Just print it out!'
        )
        self.description.save()

    def test_serialization(self):
        expected_json = ('{"content":"You need to print out Hello World!",'
                         + '"input_format":"","output_format":"The word "Hello World!" in a single line",'
                         + '"constraints":"Time: 10s","sample_input":"","sample_output":"Hello World!",'
                         + '"explanation":"Just print it out!"'
                         + '}')
        received_data = JSONRenderer().render(ChallengeDescriptionSerializer(self.description).data)

        self.assertEqual(received_data.decode('utf-8').replace('\\', ''), expected_json)


class ChallengesViewsTest(APITestCase):
    def setUp(self):
        auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        auth_user.save()
        self.auth_token = 'Token {}'.format(auth_user.auth_token.key)

        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        self.rust_lang = Language('Rust'); self.rust_lang.save()
        challenge_cat = MainCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()

    def test_view_challenge(self):
        c = Challenge(name='Hello', rating=5, score=10, test_file_name='hello_test.py',
                      test_case_count=2, category=self.sub_cat, description=self.sample_desc)
        c.save()
        c.supported_languages.add(self.rust_lang)
        response = self.client.get('/challenges/{}'.format(c.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChallengeSerializer(c).data, response.data)

    def test_view_challenge_doesnt_exist(self):
        response = self.client.get('/challenges/3', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_challenge_unauthorized_should_return_401(self):
        c = Challenge(name='Hello', rating=5, score=10, test_file_name='hello_test.py',
                      test_case_count=3, category=self.sub_cat, description=self.sample_desc)
        c.save()
        response = self.client.get('/challenges/{}'.format(c.id))

        self.assertEqual(response.status_code, 401)