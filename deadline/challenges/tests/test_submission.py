""" Tests associated with the Submission model and views """
import time
import datetime

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer

from challenges.models import Challenge, Submission, SubCategory, MainCategory, ChallengeDescription
from challenges.serializers import SubmissionSerializer, LimitedChallengeSerializer
from accounts.models import User


class SubmissionModelTest(TestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        challenge_cat = MainCategory('Tests')
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
        expected_json = ('{"id":' + str(s.id) + ',"challenge":' + str(self.challenge.id) + ',"author":"' + str(self.auth_user.username)
                         + '","code":"' + self.sample_code + '","result_score":0,"pending":true,"created_at":"' + s.created_at.isoformat()[:-6] + 'Z' + '"}')

        content = JSONRenderer().render(serializer.data)
        print(content)
        self.assertEqual(content.decode('utf-8').replace('\\n', '\n'), expected_json)


class SubmissionViewsTest(APITestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        challenge_cat = MainCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', rating=5, score=10, description=self.sample_desc, test_file_name='hello_tests',
                                   test_case_count=3, category=self.sub_cat)
        self.challenge.save()
        self.challenge_name = self.challenge.name
        self.auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        self.auth_user.save()
        self.auth_user.last_submit_at = datetime.datetime.now()-datetime.timedelta(minutes=15)
        self.auth_user.save()
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)
        self.sample_code = """prices = {'apple': 0.40, 'banana': 0.50}
        my_purchase = {
            'apple': 1,
            'banana': 6}
        grocery_bill = sum(prices[fruit] * my_purchase[fruit]
                           for fruit in my_purchase)
        print 'I owe the grocer $%.2f' % grocery_bill"""
        self.submission = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code, result_score=40)
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
        # Should order them by creation date descending
        self.assertEqual(SubmissionSerializer([second_submission, self.submission], many=True).data, response.data)

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

    def test_create_two_submissions_in_10_seconds_second_should_not_work(self):
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)

        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")'},
                                    HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'You must wait 10 more seconds before submitting a solution.')
        self.assertEqual(Submission.objects.count(), 2)

    def test_create_two_submissions_10_seconds_apart_should_not_work(self):
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)

        time.sleep(11)

        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 3)

    def test_create_submission_invalid_challenge_should_return_400(self):
        response = self.client.post('/challenges/111/submissions/new',
                                    data={'code': 'heyfriendheytherehowareyou'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)

    def test_get_top_submissions(self):
        better_submission = Submission(challenge=self.challenge, author=self.auth_user, code=self.sample_code,
                                       result_score=50)
        better_submission.save()
        # Second user with submissions
        _s_user = User(username='Seocnd user', password='123', email='EC@abv.bg', score=123); _s_user.save()
        _submission = Submission(challenge=self.challenge, author=_s_user, code=self.sample_code, result_score=50)
        top_submission = Submission(challenge=self.challenge, author=_s_user, code=self.sample_code, result_score=51)
        _submission.save();top_submission.save()

        # Should return the two submissions, (both users' best submissions) ordered by score descending
        response = self.client.get('/challenges/1/submissions/top', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        print(JSONRenderer().render(response.data))
        self.assertEqual(response.data, SubmissionSerializer([top_submission, better_submission], many=True).data)


class LatestSubmissionsViewTest(TestCase):
    def setUp(self):
        challenge_cat = MainCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()

        self.d1 = ChallengeDescription(1, 'What Up', 'Smt', 'smt', 'some', 'is', 'os', 'gotta push it to the limit')
        self.c1 = Challenge(1, 'Hello', self.d1.id, 5, 10, 'h', 3, self.sub_cat)

        self.d2 = ChallengeDescription(2, 'What Up', 'Smt', 'smt', 'some', 'is', 'os', 'gotta push it to the limit')
        self.c2 = Challenge(2, 'Second', self.d2.id, 5, 10, 'h', 3, self.sub_cat)

        self.d3 = ChallengeDescription(3, 'What Up', 'Smt', 'smt', 'some', 'is', 'os', 'gotta push it to the limit')
        self.c3 = Challenge(3, 'Third', self.d3.id, 5, 10, 'h', 3, self.sub_cat)

        self.d1.save(); self.c1.save(); self.d2.save(); self.c2.save(); self.d3.save(); self.c3.save()
        self.auth_user = User(username='123', password='123', email='123Sm2@abv.bg', score=123)
        self.auth_user.save()
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)
        self.sample_code = "print(hello)"

    def test_get_latest_challenge_submissions_from_user(self):
        """ The get_latest_submissions view should return all the latest submissions by the user distinct by their challenges"""
        s1 = Submission(challenge=self.c1, author=self.auth_user, code=self.sample_code, result_score=10)
        s1.save()
        s2 = Submission(challenge=self.c2, author=self.auth_user, code=self.sample_code, result_score=10)
        s2.save()
        s3 = Submission(challenge=self.c3, author=self.auth_user, code=self.sample_code, result_score=10)
        s3.save()
        s4 = Submission(challenge=self.c2, author=self.auth_user, code=self.sample_code, result_score=10)
        s4.save()

        """ This should return a list with c2, c3, c1 ordered like that. """
        response = self.client.get('/challenges/latest_attempted', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)

        # Hack for serializing the category
        expected_data = []
        for challenge in LimitedChallengeSerializer([self.c2, self.c3, self.c1], many=True).data:
            challenge['category'] = challenge['category'].name
            expected_data.append(challenge)
        self.assertEqual(response.data, expected_data)
