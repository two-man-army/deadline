""" Tests associated with the Submission model and views """
from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer

from challenges.models import Challenge, Submission, SubCategory, ChallengeCategory, ChallengeDescription
from challenges.serializers import SubmissionSerializer
from accounts.models import User


class SubmissionModelTest(TestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        challenge_cat = ChallengeCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', rating=5, score=10, description=self.sample_desc, test_case_count=3,
                                   category=self.sub_cat)
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
        s.save()
        serializer = SubmissionSerializer(s)
        expected_json = ('{"id":' + str(s.id) + ',"challenge":' + str(self.challenge.id) + ',"author":' + str(self.auth_user.id)
                         + ',"code":"' + self.sample_code + '","result_score":0,"pending":true}')

        content = JSONRenderer().render(serializer.data)
        self.assertEqual(content.decode('utf-8').replace('\\n', '\n'), expected_json)


class SubmissionViewsTest(APITestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        challenge_cat = ChallengeCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', rating=5, score=10, description=self.sample_desc, test_file_name='hello_tests',
                                   test_case_count=3, category=self.sub_cat)
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

    def test_view_all_submissions(self):
        second_submission = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        second_submission.save()
        response = self.client.get(path='/challenges/{}/submissions/all'.format(self.challenge.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer([self.submission, second_submission], many=True).data, response.data)

    def test_view_submission_doesnt_exist(self):
        response = self.client.get('challenges/{}/submissions/15'.format(self.submission.challenge_id)
                               , HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_submission_unauthorized_should_return_401(self):
        response = self.client.get(path=self.submission.get_absolute_url())
        self.assertEqual(response.status_code, 401)

    def test_create_submission(self):
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)
        submission = Submission.objects.get(id=2)
        # assert that the task_id has been populated
        self.assertNotEqual(submission.task_id, '')
        # assert that the test cases have been created
        self.assertEqual(submission.testcase_set.count(), submission.challenge.test_case_count)

    def test_create_submission_invalid_challenge_should_return_400(self):
        response = self.client.post('/challenges/111/submissions/new',
                                    data={'code': 'heyfriendheytherehowareyou'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)
