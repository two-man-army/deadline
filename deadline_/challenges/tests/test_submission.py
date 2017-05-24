""" Tests associated with the Submission model and views """
import time
import datetime

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer

from challenges.models import Challenge, Submission, SubCategory, MainCategory, ChallengeDescription, Language
from challenges.serializers import SubmissionSerializer, LimitedChallengeSerializer, LimitedSubmissionSerializer
from challenges.tests.factories import ChallengeFactory, SubmissionFactory, UserFactory, ChallengeDescFactory
from accounts.models import User
from unittest.mock import patch, MagicMock


class SubmissionModelTest(TestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescFactory()
        self.python_language = Language(name="Python");  self.python_language.save()
        self.rust_language = Language(name="Rust"); self.rust_language.save()
        self.sample_desc.save()
        challenge_cat = MainCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', difficulty=5, score=10, description=self.sample_desc, test_case_count=3,
                                   category=self.sub_cat)
        self.challenge.save()
        self.challenge_name = self.challenge.name

        self.auth_user = UserFactory()
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
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        s.save()

        self.assertEqual(s.get_absolute_url(), '/challenges/{}/submissions/{}'.format(s.challenge_id, s.id))

    def test_can_save_duplicate_submission(self):
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        s.save()
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        s.save()

        self.assertEqual(Submission.objects.count(), 2)

    def test_cannot_save_blank_submission(self):
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code='')
        with self.assertRaises(Exception):
            s.full_clean()

    def test_serialization(self):
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        s.save()
        serializer = SubmissionSerializer(s)
        expected_json = ('{"id":' + str(s.id) + ',"challenge":' + str(self.challenge.id) + ',"author":"' + str(self.auth_user.username)
                         + '","code":"' + self.sample_code + '","result_score":0,"pending":true,"created_at":"' + s.created_at.isoformat()[:-6] + 'Z' + '",'
                         + '"compiled":true,"compile_error_message":"","language":"Python"}')
        content = JSONRenderer().render(serializer.data)
        self.assertEqual(content.decode('utf-8').replace('\\n', '\n'), expected_json)

    def test_limited_serialization_should_not_serialize_code(self):
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                       code=self.sample_code)
        s.save()
        serializer = LimitedSubmissionSerializer(s)
        expected_json = ('{"id":' + str(s.id) + ',"challenge":' + str(self.challenge.id) + ',"author":"' + str(self.auth_user.username)
                            + '","result_score":0,"pending":true,"created_at":"' + s.created_at.isoformat()[:-6] + 'Z' + '",'
                            + '"compiled":true,"compile_error_message":"","language":"Python"}')
        content = JSONRenderer().render(serializer.data)
        self.assertEqual(content.decode('utf-8').replace('\\n', '\n'), expected_json)

    def test_fetch_top_submissions(self):
        """
        The method should return the top submissions for a given challenge,
            selecting the top submission for each user
        """
        """ Arrange """
        f_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        # Second user with submissions
        s_user = UserFactory()
        _submission = SubmissionFactory(author=s_user, challenge=self.challenge)
        top_submission = SubmissionFactory(author=s_user, challenge=self.challenge, result_score=51)
        # Third user with equal to first submission
        t_user = UserFactory()
        tr_sub = SubmissionFactory(challenge=self.challenge, author=t_user, result_score=50)

        expected_submissions = [top_submission, f_submission, tr_sub]  # ordered by score, then by date (oldest first)

        received_submissions = list(Submission.fetch_top_submissions_for_challenge(self.challenge.id))

        self.assertEqual(expected_submissions, received_submissions)

    def test_fetch_top_submissions_no_submissions_should_be_empty(self):
        received_submissions = list(Submission.fetch_top_submissions_for_challenge(self.challenge.id))
        self.assertEqual([], received_submissions)

    def test_fetch_top_submission_for_challenge_and_user_no_submissions_should_be_empty(self):
        received_submission = Submission.fetch_top_submission_for_challenge_and_user(self.challenge.id, self.auth_user.id)
        self.assertIsNone(received_submission)

    def test_fetch_top_submission_for_challenge_and_user_ignores_pending_submissions(self):
        f_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50, pending=1)
        f_submission.save()
        s_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=66, pending=1)
        s_submission.save()

        received_submission = Submission.fetch_top_submission_for_challenge_and_user(self.challenge.id,
                                                                                     self.auth_user.id)
        self.assertIsNone(received_submission)

    def test_fetch_top_submission_for_challenge_and_user_returns_bigger_score(self):
        f_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50, pending=0)
        f_submission.save()
        s_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=66, pending=0)
        s_submission.save()
        t_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=1000, pending=1)
        t_submission.save()  # IS PENDING!
        f_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=100, pending=0)
        f_submission.save()

        received_submission = Submission.fetch_top_submission_for_challenge_and_user(self.challenge.id,
                                                                                     self.auth_user.id)
        self.assertIsNotNone(received_submission)
        self.assertEqual(received_submission.maxscore, 100)

    def test_fetch_last_10_submissions_for_unique_challenges_by_author(self):
        """ The method should return the last 10 submissions for unique challenges by the author """
        for _ in range(20):
            # Create 20 submissions
            SubmissionFactory(author=self.auth_user)
        for _ in range(10):
            # Create last 10 submissions for one challenge
            SubmissionFactory(author=self.auth_user, challenge=self.challenge)

        latest_unique_submissions = Submission.fetch_last_10_submissions_for_unique_challenges_by_user(user_id=self.auth_user.id)

        # the first one should be for self.challenge, since we made it last
        self.assertEqual(latest_unique_submissions[0].challenge, self.challenge)

        # they should all be for unique challenges
        unique_challenge_ids = set([s.challenge.id for s in latest_unique_submissions])
        self.assertEqual(10, len(unique_challenge_ids))


class SubmissionViewsTest(APITestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.python_language = Language(name="Python")
        self.python_language.save()
        self.sample_desc.save()
        challenge_cat = MainCategory('Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', difficulty=5, score=10, description=self.sample_desc, test_file_name='hello_tests',
                                   test_case_count=3, category=self.sub_cat)
        self.challenge.save()
        self.challenge.supported_languages.add(self.python_language)
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
        self.submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code, result_score=10, pending=0)
        self.submission.save()

    def test_view_submission(self):
        response = self.client.get(path=self.submission.get_absolute_url(), HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer(self.submission).data, response.data)

    def test_view_own_non_solved_user_submission_should_show(self):
        """ Even though the user hasn't solved the challenge fully, it is his own so he should be able to see it"""
        aut_user2 = User(username='user2', password='user2', email='user2@abv.bg', score=123)
        aut_user2.save()
        auth_token2 = 'Token {}'.format(aut_user2.auth_token.key)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=aut_user2, pending=0,
                                code=self.sample_code, result_score=3)  # user has not solved it perfectly
        submission.save()

        response = self.client.get(path=submission.get_absolute_url(), HTTP_AUTHORIZATION=auth_token2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer(submission).data, response.data)

    def test_view_submission_non_solved_user_should_not_show(self):
        aut_user2 = User(username='user2', password='user2', email='user2@abv.bg', score=123)
        aut_user2.save()
        auth_token2 = 'Token {}'.format(aut_user2.auth_token.key)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=aut_user2, pending=0,
                                     code=self.sample_code, result_score=9)  # user has not solved it perfectly
        submission.save()

        response = self.client.get(path=self.submission.get_absolute_url(), HTTP_AUTHORIZATION=auth_token2)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'], "You have not fully solved the challenge")

    def test_view_submission_solved_user_should_show(self):
        aut_user2 = User(username='user2', password='user2', email='user2@abv.bg', score=123)
        aut_user2.save()
        auth_token2 = 'Token {}'.format(aut_user2.auth_token.key)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=aut_user2, pending=0,
                                code=self.sample_code, result_score=10)  # user has perfectly
        submission.save()

        response = self.client.get(path=self.submission.get_absolute_url(), HTTP_AUTHORIZATION=auth_token2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer(self.submission).data, response.data)

    def test_view_all_submissions(self):
        second_submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        second_submission.save()
        response = self.client.get(path='/challenges/{}/submissions/all'.format(self.challenge.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        # Should order them by creation date descending
        self.assertEqual(LimitedSubmissionSerializer([second_submission, self.submission], many=True).data, response.data)

    def test_view_all_submissions_does_not_show_code_for_submissions(self):
        second_submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code)
        second_submission.save()
        response = self.client.get(path='/challenges/{}/submissions/all'.format(self.challenge.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        for submission in response.data:
            for sub_val in submission.values():
                self.assertNotEqual(sub_val, self.sample_code)

    def test_view_submission_doesnt_exist(self):
        response = self.client.get('challenges/{}/submissions/15'.format(self.submission.challenge_id)
                               , HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_submission_unauthorized_should_return_401(self):
        response = self.client.get(path=self.submission.get_absolute_url())
        self.assertEqual(response.status_code, 401)

    def test_create_submission(self):
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)
        submission = Submission.objects.get(id=2)
        # assert that the task_id has been populated
        self.assertNotEqual(submission.task_id, '')
        # assert that the test cases have been created
        self.assertEqual(submission.testcase_set.count(), submission.challenge.test_case_count)

    def test_create_submission_invalid_language_should_return_400(self):
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Elixir'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)
        # If this test ever fails, this app must be going places
        self.assertEqual(response.data['error'], "The language Elixir is not supported!")

    def test_create_two_submissions_in_10_seconds_second_should_not_work(self):
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)

        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'You must wait 10 more seconds before submitting a solution.')
        self.assertEqual(Submission.objects.count(), 2)

    def test_create_two_submissions_10_seconds_apart_should_not_work(self):
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)

        time.sleep(11)

        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 3)

    def test_create_submission_invalid_challenge_should_return_400(self):
        response = self.client.post('/challenges/111/submissions/new',
                                    data={'code': 'heyfriendheytherehowareyou', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)

    def test_get_top_submissions(self):
        better_submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code=self.sample_code,
                                       result_score=50)
        better_submission.save()
        # Second user with submissions
        _s_user = User(username='Seocnd user', password='123', email='EC@abv.bg', score=123); _s_user.save()
        _submission = Submission(language=self.python_language, challenge=self.challenge, author=_s_user, code=self.sample_code, result_score=50)
        top_submission = Submission(language=self.python_language, challenge=self.challenge, author=_s_user, code=self.sample_code, result_score=51)
        _submission.save();top_submission.save()

        # Should return the two submissions, (both users' best submissions) ordered by score descending
        response = self.client.get('/challenges/1/submissions/top', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, LimitedSubmissionSerializer([top_submission, better_submission], many=True).data)

    def test_get_top_submissions_invalid_id(self):
        response = self.client.get('/challenges/33/submissions/top', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], f'Invalid challenge id 33!')

    @patch('challenges.models.Submission.fetch_top_submissions_for_challenge')
    def test_get_top_submissions_calls_Submission_method(self, mock_top_submissions):
        """ Should call the submissions method for fetching the top challenges """
        self.client.get('/challenges/1/submissions/top', HTTP_AUTHORIZATION=self.auth_token)
        mock_top_submissions.assert_called_once_with(challenge_id=str(self.challenge.id))

    def test_get_self_top_submission(self):
        """ Should return the user's top submission """
        new_user = User(username='1223', password='123', email='12223@abv.bg', score=123)
        new_user.save()
        new_auth_token = 'Token {}'.format(new_user.auth_token.key)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=new_user,
                                     code=self.sample_code, result_score=5, pending=0)
        submission.save()
        top_submission = Submission(language=self.python_language, challenge=self.challenge, author=new_user,
                                code=self.sample_code, result_score=6, pending=0)
        top_submission.save()
        sec_submission = Submission(language=self.python_language, challenge=self.challenge, author=new_user,
                                code=self.sample_code, result_score=5, pending=0)
        sec_submission.save()

        response = self.client.get(f'/challenges/{self.challenge.id}/submissions/selfTop', HTTP_AUTHORIZATION=new_auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, LimitedSubmissionSerializer(top_submission).data)

    def test_get_self_top_submission_no_submission(self):
        """ Should return 404 """
        new_user = User(username='1223', password='123', email='12223@abv.bg', score=123)
        new_user.save()
        new_auth_token = 'Token {}'.format(new_user.auth_token.key)

        response = self.client.get(f'/challenges/{self.challenge.id}/submissions/selfTop', HTTP_AUTHORIZATION=new_auth_token)

        self.assertEqual(response.status_code, 404)

    def test_get_self_top_submission_requires_auth(self):
        self.assertEqual(self.client.get(f'/challenges/{self.challenge.id}/submissions/selfTop').status_code, 401)

    def test_get_self_top_submission_invalid_challenge_id(self):
        """/challenges/(?P<challenge_pk>\d+)/submissions/selfTop"""
        response = self.client.get(f'/challenges/255/submissions/selfTop', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 400)

    @patch('challenges.models.Submission.fetch_top_submission_for_challenge_and_user')
    def test_get_self_top_submission_calls_Submission_method(self, mock_top_submission):
        """Should call the submission's method """
        mock_top_submission.return_value = self.submission

        self.client.get(f'/challenges/{self.challenge.id}/submissions/selfTop', HTTP_AUTHORIZATION=self.auth_token)

        mock_top_submission.assert_called_once_with(challenge_id=str(self.challenge.id), user_id=self.auth_user.id)


class LatestSubmissionsViewTest(TestCase):
    def setUp(self):
        challenge_cat = MainCategory('Tests')
        challenge_cat.save()
        self.python_language = Language(name="Python"); self.python_language.save()

        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()

        self.c1 = ChallengeFactory(category=self.sub_cat)
        self.c2 = ChallengeFactory(category=self.sub_cat)
        self.c3 = ChallengeFactory(category=self.sub_cat)

        self.auth_user = User(username='123', password='123', email='123Sm2@abv.bg', score=123)
        self.auth_user.save()
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)
        self.sample_code = "print(hello)"

    def test_get_latest_challenge_submissions_from_user(self):
        """ The get_latest_submissions view should return all the latest submissions by the user distinct by their challenges"""
        s1 = SubmissionFactory(author=self.auth_user, challenge=self.c1, pending=0)
        s2 = SubmissionFactory(author=self.auth_user, challenge=self.c2, pending=0)
        s3 = SubmissionFactory(author=self.auth_user, challenge=self.c3, pending=0)
        s4 = SubmissionFactory(author=self.auth_user, challenge=self.c2, pending=0)
        # s1.save;s2.save;s3.save;s4.save;  # view queries for the best submission
        self.c1.user_max_score = s1.result_score
        self.c3.user_max_score = s3.result_score
        self.c2.user_max_score = max(s2.result_score, s4.result_score)
        """ This should return a list with c2, c3, c1 ordered like that. """
        expected_data = LimitedChallengeSerializer([self.c2, self.c3, self.c1], many=True, context={'request': MagicMock(user=self.auth_user)}).data

        response = self.client.get('/challenges/latest_attempted', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        # Hack for serializing the category
        self.assertCountEqual(response.data, expected_data)
        self.assertEqual(response.data, expected_data)

    @patch('challenges.models.Submission.fetch_last_10_submissions_for_unique_challenges_by_user')
    def test_assert_called_submission_method(self, method_mock):
        """ Assert that the function calls the submission method"""
        self.client.get('/challenges/latest_attempted', HTTP_AUTHORIZATION=self.auth_token)
        method_mock.assert_called_once_with(user_id=self.auth_user.id)
