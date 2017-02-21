""" Tests associated with the Challenge model and views """
from django.test import TestCase
from django.utils.six import BytesIO
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from challenges.models import Challenge
from challenges.serializers import ChallengeSerializer
from accounts.models import User


class ChallengesModelTest(TestCase):
    def test_absolute_url(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up', test_case_count=5)
        expected_url = '/challenges/{}'.format(c.id)
        self.assertEqual(c.get_absolute_url(), expected_url)

    def test_cannot_save_duplicate_challenge(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up', test_case_count=5)
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge(name='Hello', rating=5, score=10, description='What up', test_case_count=5)
            c.full_clean()

    def test_cannot_save_blank_challenge(self):
        c = Challenge()
        with self.assertRaises(Exception):
            c.full_clean()

    def test_serialization(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up', test_case_count=5)
        expected_json = '{"name":"Hello","rating":5,"score":10,"description":"What up","test_case_count":5}'

        content = JSONRenderer().render(ChallengeSerializer(c).data)
        self.assertEqual(content.decode('utf-8'), expected_json)

    def test_deserialization(self):
        expected_json = b'{"name":"Hello","rating":5,"score":10,"description":"What up","test_case_count":3}'
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


class ChallengesViewsTest(APITestCase):
    def setUp(self):
        auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        auth_user.save()
        self.auth_token = 'Token {}'.format(auth_user.auth_token.key)

    def test_view_challenge(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up', test_file_name='hello_test.py',
                      test_case_count=2)
        c.save()
        response = self.client.get('/challenges/{}'.format(c.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChallengeSerializer(c).data, response.data)

    def test_view_challenge_doesnt_exist(self):
        response = self.client.get('/challenges/3', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_challenge_unauthorized_should_return_401(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up', test_file_name='hello_test.py',
                      test_case_count=3)
        c.save()
        response = self.client.get('/challenges/{}'.format(c.id))

        self.assertEqual(response.status_code, 401)