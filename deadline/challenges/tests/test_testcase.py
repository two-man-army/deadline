""" Tests associated with the TestCase model and views """
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer

from challenges.models import Challenge, Submission, TestCase as TestCaseModel, ChallengeCategory, SubCategory
from challenges.serializers import TestCaseSerializer
from accounts.models import User


class TestCaseViewTest(APITestCase):
    def setUp(self):
        challenge_cat = ChallengeCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', rating=5, score=10, description='What up', test_case_count=2,
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
        self.submission = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        self.submission.save()
        self.tc = TestCaseModel(submission=self.submission, pending=False, success=True, time='1.25s')
        self.tc_2 = TestCaseModel(submission=self.submission)
        self.tc_3 = TestCaseModel(submission=self.submission, pending=False, success=False, time='0.2s')
        self.tc.save(); self.tc_2.save(); self.tc_3.save()

    def test_load_all_test_cases(self):
        response = self.client.get('/challenges/{}/submissions/{}/tests'.format(self.challenge.id, self.submission.id),
                                   HTTP_AUTHORIZATION=self.auth_token)
        serializer = TestCaseSerializer(self.submission.testcase_set, many=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(serializer.data, response.data)

    def test_load_all_test_cases_invalid_challenge_should_400(self):
        response = self.client.get('/challenges/11/submissions/{}/tests'.format(self.submission.id),
                                   HTTP_AUTHORIZATION=self.auth_token)

        expected_error_msg = 'No testcases were found, the given challenge or submission ID is most likely invalid'
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], expected_error_msg)

    def test_load_all_test_cases_invalid_submission_should_400(self):
        response = self.client.get('/challenges/{}/submissions/15/tests'.format(self.challenge.id),
                                   HTTP_AUTHORIZATION=self.auth_token)
        expected_error_msg = 'No testcases were found, the given challenge or submission ID is most likely invalid'
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], expected_error_msg)

    def test_load_single_test_case(self):
        response = self.client.get(self.tc.get_absolute_url(), HTTP_AUTHORIZATION=self.auth_token)
        serializer = TestCaseSerializer(self.tc)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(serializer.data, response.data)

    def test_load_invalid_test_case_should_return_404(self):
        response = self.client.get('/challenges/{}/submissions/{}/test/44'.format(self.challenge.id, self.submission.id),
                                   HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_load_single_test_case_invalid_submission_id(self):
        response = self.client.get(
            '/challenges/{}/submissions/111/test/{}'.format(self.challenge.id, self.tc.id),
            HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)

    def test_load_single_test_case_invalid_challenge_id_should_400(self):
        response = self.client.get(
            '/challenges/111/submissions/{}/test/{}'.format(self.submission.id, self.tc.id),
            HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)

    def test_load_test_case_unauthorized_should_return_401(self):
        response = self.client.get(self.tc.get_absolute_url())

        self.assertEqual(response.status_code, 401)


class TestCaseModelTest(TestCase):
    def setUp(self):
        challenge_cat = ChallengeCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', rating=5, score=10, description='What up', test_case_count=5,
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
        tc = TestCaseModel(submission=self.submission, pending=False, success=True, time='1.25s', description='Testing', traceback='You suck at coding', error_message="whatup")
        tc.save()
        expected_json = '{"submission":' + str(tc.submission.id) + ',"pending":false,"success":true,"time":"1.25s","description":"Testing","traceback":"You suck at coding","error_message":"whatup"}'
        serialized_test_case: bytes = JSONRenderer().render(data=TestCaseSerializer(tc).data)

        self.assertEqual(serialized_test_case.decode('utf-8'), expected_json)