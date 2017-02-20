from django.test import TestCase
from django.core.exceptions import ValidationError

from django.utils.six import BytesIO
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from challenges.models import Challenge, Submission, TestCase as TestCaseModel
from challenges.serializers import ChallengeSerializer, SubmissionSerializer, TestCaseSerializer
from accounts.models import User


# Create your tests here.
class ChallengesModelTest(TestCase):
    def test_absolute_url(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up')
        expected_url = '/challenges/{}'.format(c.id)
        self.assertEqual(c.get_absolute_url(), expected_url)

    def test_cannot_save_duplicate_challenge(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up')
        c.save()
        with self.assertRaises(ValidationError):
            c = Challenge(name='Hello', rating=5, score=10, description='What up')
            c.full_clean()

    def test_cannot_save_blank_challenge(self):
        c = Challenge()
        with self.assertRaises(Exception):
            c.full_clean()

    def test_serialization(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up')
        expected_json = '{"name":"Hello","rating":5,"score":10,"description":"What up"}'

        content = JSONRenderer().render(ChallengeSerializer(c).data)
        self.assertEqual(content.decode('utf-8'), expected_json)

    def test_deserialization(self):
        expected_json = b'{"name":"Hello","rating":5,"score":10,"description":"What up"}'
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
        c = Challenge(name='Hello', rating=5, score=10, description='What up')
        c.save()
        response = self.client.get('/challenges/{}'.format(c.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChallengeSerializer(c).data, response.data)

    def test_view_challenge_doesnt_exist(self):
        response = self.client.get('/challenges/3', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_challenge_unauthorized_should_return_401(self):
        c = Challenge(name='Hello', rating=5, score=10, description='What up')
        c.save()
        response = self.client.get('/challenges/{}'.format(c.id))

        self.assertEqual(response.status_code, 401)


class SubmissionViewsTest(APITestCase):
    def setUp(self):
        self.challenge = Challenge(name='Hello', rating=5, score=10, description='What up')
        self.challenge.save()
        self.challenge_name = self.challenge.name

        self.auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        self.auth_user.save()
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)
        self.sample_code = """prices = {'apple': 0.40, 'banana': 0.50}
        my_purchase = {
            'apple': 1,
            'banana': 6}
        grocery_bill = sum(prices[fruit] * my_purchase[fruit]
                           for fruit in my_purchase)
        print 'I owe the grocer $%.2f' % grocery_bill"""
        self.submission = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        self.submission.save()

    def test_view_submission(self):
        response = self.client.get(path=self.submission.get_absolute_url(), HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer(self.submission).data, response.data)

    def test_view_submission_doesnt_exist(self):
        response = self.client.get('challenges/{}/submissions/15'.format(self.submission.challenge_id)
                               , HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_challenge_unauthorized_should_return_401(self):
        response = self.client.get(path=self.submission.get_absolute_url())
        self.assertEqual(response.status_code, 401)


class SubmissionModelTest(TestCase):
    def setUp(self):
        self.challenge = Challenge(name='Hello', rating=5, score=10, description='What up')
        self.challenge.save()
        self.challenge_name = self.challenge.name

        self.auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        self.auth_user.save()
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)
        self.sample_code = """prices = {'apple': 0.40, 'banana': 0.50}
my_purchase = {
    'apple': 1,
    'banana': 6}
grocery_bill = sum(prices[fruit] * my_purchase[fruit]
                   for fruit in my_purchase)
print 'I owe the grocer $%.2f' % grocery_bill"""

    def test_absolute_url(self):
        s = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        s.save()

        self.assertEqual(s.get_absolute_url(), '/challenges/{}/submissions/{}'.format(s.challenge_id, s.id))

    def test_can_save_duplicate_submission(self):
        s = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        s.save()
        s = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        s.save()

        self.assertEqual(Submission.objects.count(), 2)

    def test_cannot_save_blank_submission(self):
        s = Submission(challenge=self.challenge, author=self.auth_user, code='')
        with self.assertRaises(Exception):
            s.full_clean()

    def test_serialization(self):
        s = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        serializer = SubmissionSerializer(s)
        expected_json = ('{"challenge":' + str(self.challenge.id) + ',"author":' + str(self.auth_user.id)
                         + ',"code":"' + self.sample_code + '"}')

        content = JSONRenderer().render(serializer.data)
        self.assertEqual(content.decode('utf-8').replace('\\n', '\n'), expected_json)


class TestCaseModelTest(TestCase):
    def setUp(self):
        self.challenge = Challenge(name='Hello', rating=5, score=10, description='What up')
        self.challenge.save()
        self.challenge_name = self.challenge.name

        self.auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        self.auth_user.save()
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)
        self.sample_code = """prices = {'apple': 0.40, 'banana': 0.50}
            my_purchase = {
                'apple': 1,
                'banana': 6}
            grocery_bill = sum(prices[fruit] * my_purchase[fruit]
                               for fruit in my_purchase)
            print 'I owe the grocer $%.2f' % grocery_bill"""
        self.submission = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        self.submission.save()

    def test_absolute_url(self):
        tc = TestCaseModel(submission=self.submission)
        tc.save()

        self.assertEqual(tc.get_absolute_url(), '/challenges/{}/submissions/{}/test/{}'.format(
            tc.submission.challenge_id,tc.submission.id, tc.id))

    def test_can_have_multiple_testcases_per_submission(self):
        for _ in range(15):
            tc = TestCaseModel(submission=self.submission)
            tc.save()

        self.assertEqual(TestCaseModel.objects.count(), 15)
        # Assert they all point to the same submission
        for tc in TestCaseModel.objects.all():
            self.assertEqual(tc.submission.id, self.submission.id)

    def test_field_defaults(self):
        """ Should have it time set to 0, pending to True, success to False"""
        tc = TestCaseModel(submission=self.submission)
        tc.save()

        self.assertEqual(tc.time, '0.00s')
        self.assertTrue(tc.pending)
        self.assertFalse(tc.success)

    def test_serialize(self):
        tc = TestCaseModel(submission=self.submission, pending=False, success=True, time='1.25s')
        tc.save()
        expected_json = '{"submission":' + str(tc.submission.id) + ',"pending":false,"success":true,"time":"1.25s"}'
        serialized_test_case: bytes = JSONRenderer().render(data=TestCaseSerializer(tc).data)

        self.assertEqual(serialized_test_case.decode('utf-8'), expected_json)