from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils.six import BytesIO
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from accounts.models import User
from accounts.serializers import UserSerializer
from challenges.tests.factories import UserFactory, ChallengeDescFactory


# Create your tests here.
class UserModelTest(TestCase):
    def test_user_register_creates_token(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
        self.assertTrue(hasattr(us, 'auth_token'))
        self.assertIsNotNone(us.auth_token)

    def test_user_register_requires_unique_username(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
        us.save()
        with self.assertRaises(Exception):
            us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
            us.save()

    def test_serialization(self):
        """ Should convert a user object to a json """
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
        # password should be hashed
        expected_json = '{"id":1,"username":"SomeGuy","email":"me@abv.bg","password":"%s","score":123}' % (us.password)

        content = JSONRenderer().render(UserSerializer(us).data)
        self.assertEqual(content.decode('utf-8'), expected_json)

    def test_deserialization(self):
        expected_json = b'{"id":1,"username":"SomeGuy","email":"me@abv.bg","password":"123","score":123}'

        data = JSONParser().parse(BytesIO(expected_json))
        serializer = UserSerializer(data=data)

        serializer.is_valid()
        deser_user = serializer.save()

        self.assertIsInstance(deser_user, User)
        self.assertEqual(deser_user.username, 'SomeGuy')
        self.assertEqual(deser_user.email, 'me@abv.bg')
        self.assertNotEqual(deser_user.password, '123')  # should be hashed!
        self.assertEqual(deser_user.score, 123)

    def test_get_vote_for_submission_returns_vote(self):
        from challenges.models import Challenge, Submission, SubCategory, MainCategory, ChallengeDescription, Language, \
            SubmissionVote
        python_language = Language(name="Python") ;python_language.save()
        challenge_cat = MainCategory('Tests'); challenge_cat.save()
        sub_cat = SubCategory(name='tests', meta_category=challenge_cat); sub_cat.save()
        challenge = Challenge(name='Hello', difficulty=5, score=10, description=ChallengeDescFactory(),
                                   test_case_count=3,
                                   category=sub_cat); challenge.save()
        auth_user = UserFactory()
        auth_user.save()
        s = Submission(language=python_language, challenge=challenge, author=auth_user,
                       code='a')
        s.save()
        sv1 = SubmissionVote(author=auth_user, submission=s, is_upvote=False)
        sv1.save()

        received_vote = auth_user.get_vote_for_submission(submission_id=s.id)
        self.assertEqual(received_vote, sv1)

    def test_get_vote_for_submission_no_vote_returns_None(self):
        auth_user = UserFactory()
        self.assertIsNone(auth_user.get_vote_for_submission(submission_id=1))

    @patch('challenges.models.Submission.fetch_top_submission_for_challenge_and_user')
    def test_fetch_max_score_for_challenge(self, fetch_mock):
        """ Should call the submission's fetch_top_submission method"""
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
        us.save()
        fetch_mock.return_value = MagicMock(maxscore=5)

        received_score = us.fetch_max_score_for_challenge(1)

        fetch_mock.assert_called_once_with(1, us.id)
        self.assertEqual(received_score, 5)


    @patch('challenges.models.Submission.fetch_top_submission_for_challenge_and_user')
    def test_fetch_max_score_for_challenge_return_0_on_none_value(self, fetch_mock):
        """ Should return 0 if no such score exists"""
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
        us.save()
        fetch_mock.return_value = None

        received_score = us.fetch_max_score_for_challenge(1)

        fetch_mock.assert_called_once_with(1, us.id)
        self.assertEqual(received_score, 0)


class RegisterViewTest(APITestCase):
    def test_register(self):
        # The user posts his username, email and password to the /accounts/register URL
        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'meredith@abv.bg'})
        # Should have successfully register the user and gave him a user token
        self.assertEqual(response.status_code, 201)
        self.assertTrue('user_token' in response.data)

    def test_register_existing_user_should_return_400(self):
        User.objects.create(email='that_part@abv.bg', password='123', username='ThatPart')

        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'that_part@abv.bg'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertIn('email already exists', ''.join(response.data['email']))

    def test_register_existing_username_should_return_400(self):
        User.objects.create(email='that_part@abv.bg', password='123', username='ThatPart')
        # User.objects.create(email='smthh_aa@abv.bg', password='123', username='ThatPart')

        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'ThatPart',
                                                                               'password': 'mer19222',
                                                                               'email': 'TANKTNAK@abv.bg'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data)
        self.assertIn('username already exists', ''.join(response.data['username']))


class LoginViewTest(APITestCase):
    def test_logging_in_valid(self):
        # There is a user account
        User.objects.create(email='that_part@abv.bg', password='123')
        # And we try logging in to it
        response: HttpResponse = self.client.post('/accounts/login/', data={'email': 'that_part@abv.bg',
                                                                            'password': '123'})
        self.assertEqual(response.status_code, 202)
        self.assertTrue('user_token' in response.data)

    def test_logging_in_invalid_email(self):
        # There is a user account
        User.objects.create(email='that_part@abv.bg', password='123')
        # And we try logging in to it
        response: HttpResponse = self.client.post('/accounts/login/', data={'email': 'INVALID_EMAIL',
                                                                            'password': '123'})

        self.assertEqual(response.status_code, 400)
        # the response should return an error that the email is invalid
        self.assertIn('error', response.data)
        self.assertIn('Invalid credentials', ''.join(response.data['error']))
