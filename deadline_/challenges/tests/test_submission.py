""" Tests associated with the Submission model and views """
import time
import datetime
from random import randint
from collections import OrderedDict
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase

from accounts.serializers import UserSerializer
from challenges.models import (Challenge, Submission, SubCategory, MainCategory, Language, SubmissionVote,
                               Proficiency, SubmissionComment)
from challenges.serializers import SubmissionSerializer, LimitedChallengeSerializer, LimitedSubmissionSerializer, \
    SubmissionCommentSerializer
from challenges.tests.factories import ChallengeFactory, SubmissionFactory, UserFactory, ChallengeDescFactory
from challenges.tests.base import TestHelperMixin
from accounts.models import User
from challenges.views import SubmissionCommentCreateView
from social.constants import RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION, \
    RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION
from social.models.notification import Notification


class SubmissionModelTest(TestCase, TestHelperMixin):
    def setUp(self):
        self.sample_desc = ChallengeDescFactory()
        self.python_language = Language.objects.create(name="Python")
        self.rust_language = Language.objects.create(name="Rust")
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.challenge = Challenge.objects.create(name='Hello', difficulty=5, score=10, description=self.sample_desc,
                                                  test_case_count=3, category=self.sub_cat)
        self.challenge_name = self.challenge.name

        self.create_user_and_auth_token()

    def test_absolute_url(self):
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="")
        s.save()

        self.assertEqual(s.get_absolute_url(), '/challenges/{}/submissions/{}'.format(s.challenge_id, s.id))

    def test_can_save_duplicate_submission(self):
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="")
        s.save()
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="")
        s.save()

        self.assertEqual(Submission.objects.count(), 2)

    def test_cannot_save_blank_submission(self):
        s = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code='')
        with self.assertRaises(Exception):
            s.full_clean()

    def test_has_solved_challenge_should_return_true_when_solved(self):
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                      code="", result_score=self.challenge.score, pending=False)
        self.assertTrue(s.has_solved_challenge())

    def test_has_solved_challenge_should_return_false_when_not_solved(self):
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                      code="", result_score=self.challenge.score-1, pending=False)
        self.assertFalse(s.has_solved_challenge())

    def test_has_solved_challenge_should_return_false_when_still_pending(self):
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                      code="", result_score=self.challenge.score, pending=True)
        self.assertFalse(s.has_solved_challenge())

    def test_fetch_top_submissions(self):
        """
        The method should return the top submissions for a given challenge,
            selecting the top submission for each user
        """
        """ Arrange """
        f_submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        # Second user with submissions
        s_user = UserFactory()
        SubmissionFactory(author=s_user, challenge=self.challenge)  # should get ignored
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
        SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50, pending=True)
        SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=66, pending=True)

        received_submission = Submission.fetch_top_submission_for_challenge_and_user(self.challenge.id,
                                                                                     self.auth_user.id)
        # should return None as there is no top submission
        self.assertIsNone(received_submission)

    def test_fetch_top_submission_for_challenge_and_user_returns_bigger_score(self):
        SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50, pending=False)
        SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=66, pending=False)
        # IS PENDING!
        SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=1000, pending=True)
        SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=100, pending=False)

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

    def test_get_votes_count(self):
        """
        Get votes count should return a tuple indicating the upvote and downvote count
        for the given SubmissionVote object
        """
        sec_user = UserFactory()
        third_user = UserFactory()
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="")
        SubmissionVote.objects.create(author=self.auth_user, submission=s, is_upvote=False)
        SubmissionVote.objects.create(author=sec_user, submission=s, is_upvote=True)
        SubmissionVote.objects.create(author=third_user, submission=s, is_upvote=False)
        self.assertEqual((1, 2), s.get_votes_count())

    def test_get_votes_no_votes_returns_0(self):
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                       code="")
        self.assertEqual((0, 0), s.get_votes_count())

    def test_get_votes_with_delete_returns_expected(self):
        sec_user = UserFactory()
        third_user = UserFactory()
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                      code="")
        sv1 = SubmissionVote.objects.create(author=self.auth_user, submission=s, is_upvote=False)
        sv2 = SubmissionVote.objects.create(author=sec_user, submission=s, is_upvote=True)
        sv3 = SubmissionVote.objects.create(author=third_user, submission=s, is_upvote=False)
        self.assertEqual((1, 2), s.get_votes_count())

        sv3.delete()
        self.assertEqual((1, 1), s.get_votes_count())
        sv2.delete()
        self.assertEqual((0, 1), s.get_votes_count())
        sv1.delete()
        self.assertEqual((0, 0), s.get_votes_count())

    def test_fetch_submissions_from_user_since_returns_only_submissions_created_on_or_after_that_date(self):
        start_date = datetime.date(2017, 10, 12)
        # four submissions since that date, and three before
        for i in range(7):
            if i % 2 == 0:
                s = SubmissionFactory(author=self.auth_user, pending=False)
                self.update_model(s, created_at=start_date + datetime.timedelta(days=randint(0, 1)))
            else:
                s = SubmissionFactory(author=self.auth_user, pending=False)
                self.update_model(s, created_at=start_date - datetime.timedelta(days=randint(1, 10)))

        received_subs = Submission.fetch_submissions_from_user_since(user=self.auth_user, since_date=start_date)

        self.assertEqual(len(received_subs), 4)

    def test_fetch_submissions_from_user_since_returns_only_non_pending_submissions(self):
        start_date = datetime.date(2017, 10, 12)
        s = SubmissionFactory(author=self.auth_user, pending=True)
        self.update_model(s, created_at=start_date + datetime.timedelta(days=randint(0, 1)))

        received_subs = Submission.fetch_submissions_from_user_since(user=self.auth_user, since_date=start_date)

        self.assertEqual(len(received_subs), 0)

    def test_fetch_submissions_count_from_user_since_returns_only_submissions_created_on_or_after_that_date(self):
        start_date = datetime.date(2017, 10, 12)
        second_date = start_date + datetime.timedelta(days=1)
        # four submissions since that date and 6 before
        for i in range(10):
            if i > 3:
                s = SubmissionFactory(author=self.auth_user, pending=False)
                self.update_model(s, created_at=start_date - datetime.timedelta(days=1))
            elif i % 2 == 0:
                s = SubmissionFactory(author=self.auth_user, pending=False)
                self.update_model(s, created_at=start_date)
            else:
                s = SubmissionFactory(author=self.auth_user, pending=False)
                self.update_model(s, created_at=second_date)
        expected_data = [{'created_at': start_date, 'count': 2}, {'created_at': second_date, 'count': 2}]

        received_data = list(Submission.fetch_submissions_count_by_day_from_user_since(self.auth_user, start_date))

        self.assertEqual(expected_data, received_data)

    def fetch_submissions_count_by_day_from_user_since_groups_by_day(self):
        start_date = datetime.date(2017, 10, 12)
        # Create 4 different submissions in different hours/minutes
        for i in range(4):
            s = SubmissionFactory(author=self.auth_user, pending=False)
            self.update_model(s, created_at=start_date + datetime.timedelta(hours=i))
        expected_data = [{'created_at': start_date, 'count': 4}]

        received_data = list(Submission.fetch_submissions_count_by_day_from_user_since(self.auth_user, start_date))

        self.assertEqual(expected_data, received_data)

    def test_fetch_submissions_count_from_user_since_returns_only_non_pending_submissions_count(self):
        start_date = datetime.date(2017, 10, 12)
        s = SubmissionFactory(author=self.auth_user, pending=True)
        self.update_model(s, created_at=start_date + datetime.timedelta(days=randint(0, 1)))
        expected_data = []

        received_data = list(Submission.fetch_submissions_count_by_day_from_user_since(self.auth_user, start_date))

        self.assertEqual(expected_data, received_data)


class SubmissionCommentModelViewTest(TestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    def test_nested_serialization(self):
        author_data = OrderedDict(UserSerializer(instance=self.auth_user).data)
        first_comment = SubmissionComment.objects.create(submission=self.submission,
                                                         author=self.auth_user, content='corridor')
        first_reply = SubmissionComment.objects.create(submission=self.submission, parent=first_comment,
                                                       author=self.auth_user, content='night call')
        second_reply = SubmissionComment.objects.create(submission=self.submission, parent=first_comment,
                                                        author=self.auth_user, content='soldier')
        second_reply_reply = SubmissionComment.objects.create(submission=self.submission, parent=second_reply,
                                                        author=self.auth_user, content='wall')
        first_reply_reply = SubmissionComment.objects.create(submission=self.submission, parent=first_reply,
                                                              author=self.auth_user, content='ice')
        first_reply_reply_reply = SubmissionComment.objects.create(submission=self.submission, parent=first_reply_reply,
                                                                     author=self.auth_user, content='vens')

        # Also asserts that they are ordered by creation date
        expected_data = {
            'id': first_comment.id,
            'content': first_comment.content,
            'author': author_data,
            'replies': [
                {
                    'id': second_reply.id,
                    'content': second_reply.content,
                    'author': author_data,
                    'replies': [
                        {
                            'id': second_reply_reply.id,
                            'content': second_reply_reply.content,
                            'author': author_data,
                            'replies': [],
                        }
                    ],
                },
                {
                    'id': first_reply.id,
                    'content': first_reply.content,
                    'author': author_data,
                    'replies': [
                        {
                            'id': first_reply_reply.id,
                            'content': first_reply_reply.content,
                            'author': author_data,
                            'replies': [
                                {
                                    'id': first_reply_reply_reply.id,
                                    'content': first_reply_reply_reply.content,
                                    'author': author_data,
                                    'replies': [],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        received_data = SubmissionCommentSerializer(first_comment).data
        self.assertEqual(expected_data, received_data)

    def test_add_comment_adds_comment_and_creates_notification(self):
        f_submission: Submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        us = UserFactory()
        f_submission.add_comment(author=us, content='Hello')

        self.assertEqual(f_submission.comments.count(), 1)
        self.assertEqual(f_submission.comments.first().author, us)
        self.assertEqual(f_submission.comments.first().content, 'Hello')
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)

    def test_add_comment_doesnt_create_notification_if_specified(self):
        f_submission: Submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        f_submission.add_comment(author=UserFactory(), content='Hello', to_notify=False)
        self.assertEqual(Notification.objects.count(), 0)

    def test_add_comment_doesnt_create_notification_if_submission_author_comments_himself(self):
        f_submission: Submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        f_submission.add_comment(author=self.auth_user, content='Hello', to_notify=True)
        self.assertEqual(Notification.objects.count(), 0)

    def test_add_reply_adds_reply(self):
        f_submission: Submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        sb_comment = SubmissionComment.objects.create(submission=f_submission, author=self.auth_user, content='aa')

        sb_comment.add_reply(author=UserFactory(), content='Light it up')
        self.assertEqual(sb_comment.replies.count(), 1)
        self.assertEqual(sb_comment.replies.first().content, 'Light it up')
        # should also create a notification
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().type, RECEIVE_SUBMISSION_COMMENT_REPLY_NOTIFICATION)

    def test_add_reply_doesnt_create_notif_if_commenter_is_replier(self):
        f_submission: Submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        sb_comment = SubmissionComment.objects.create(submission=f_submission, author=self.auth_user, content='aa')
        sb_comment.add_reply(self.auth_user, content='Light it up', to_notify=True)
        self.assertEqual(Notification.objects.count(), 0)

    def test_add_reply_doesnt_create_notif_if_specified(self):
        f_submission: Submission = SubmissionFactory(author=self.auth_user, challenge=self.challenge, result_score=50)
        sb_comment = SubmissionComment.objects.create(submission=f_submission, author=self.auth_user, content='aa')

        sb_comment.add_reply(author=UserFactory(), content='Light it up', to_notify=False)
        self.assertEqual(Notification.objects.count(), 0)


# TODO: Split tests to test the function validate_data() instead of issuing a request
# TODO:     + a mock ot assure its called when issuing a request
class SubmissionViewsTest(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()
        self.auth_user.last_submit_at = datetime.datetime.now()-datetime.timedelta(minutes=15)
        self.auth_user.save()

    def test_view_submission(self):
        response = self.client.get(path=self.submission.get_absolute_url(), HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer(self.submission).data, response.data)

    # Test Submission Details view privileges

    def test_view_own_non_solved_user_submission_should_show(self):
        """ Even though the user hasn't solved the challenge fully, it is his own so he should be able to see it"""
        aut_user2 = User.objects.create(username='user2', password='user2', email='user2@abv.bg', score=123, role=self.base_role)
        auth_token2 = 'Token {}'.format(aut_user2.auth_token.key)
        submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=aut_user2, pending=0,
                                               code="", result_score=3)  # user has not solved it perfectly

        response = self.client.get(path=submission.get_absolute_url(), HTTP_AUTHORIZATION=auth_token2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer(submission).data, response.data)

    def test_view_submission_non_solved_user_should_not_show(self):
        aut_user2 = User.objects.create(username='user2', password='user2', email='user2@abv.bg', score=123,
                                        role=self.base_role)
        auth_token2 = 'Token {}'.format(aut_user2.auth_token.key)
        Submission.objects.create(language=self.python_language, challenge=self.challenge, author=aut_user2,
                                  pending=False, code="", result_score=9)  # user has not solved it perfectly

        response = self.client.get(path=self.submission.get_absolute_url(), HTTP_AUTHORIZATION=auth_token2)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'], "You have not fully solved the challenge")

    def test_view_submission_solved_user_should_show(self):
        aut_user2 = User.objects.create(username='user2', password='user2', email='user2@abv.bg', score=123, role=self.base_role)
        auth_token2 = 'Token {}'.format(aut_user2.auth_token.key)
        Submission.objects.create(language=self.python_language, challenge=self.challenge, author=aut_user2,
                                  pending=False, code="", result_score=10)  # user has solved it perfectly

        response = self.client.get(path=self.submission.get_absolute_url(), HTTP_AUTHORIZATION=auth_token2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubmissionSerializer(self.submission).data, response.data)

    # Test Submission Details view privileges ^

    def test_view_all_submissions(self):
        second_submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="")
        second_submission.save()
        response = self.client.get(path='/challenges/{}/submissions/all'.format(self.challenge.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        # Should order them by creation date descending
        self.assertEqual(LimitedSubmissionSerializer([second_submission, self.submission], many=True).data, response.data)

    def test_view_all_submissions_does_not_show_code_for_submissions(self):
        second_submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="time")
        second_submission.save()
        response = self.client.get(path='/challenges/{}/submissions/all'.format(self.challenge.id), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        for submission in response.data:
            self.assertNotIn('code', submission.keys())

    def test_view_submission_doesnt_exist(self):
        response = self.client.get('challenges/{}/submissions/15'.format(self.submission.challenge_id)
                               , HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_view_submission_unauthorized_should_return_401(self):
        response = self.client.get(path=self.submission.get_absolute_url())
        self.assertEqual(response.status_code, 401)

    @patch('challenges.views.run_grader_task.delay')
    def test_create_submission(self, mock_delay):
        mock_delay.return_value = 1
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/new',
                                    data={'code': 'print("Hello World")', 'language': self.python_language.name},
                                    HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)
        submission = Submission.objects.last()
        # assert that the task_id has been populated
        self.assertEqual(submission.task_id, '1')
        # assert that the test cases have been created
        self.assertEqual(submission.testcase_set.count(), submission.challenge.test_case_count)

    @patch('challenges.views.run_grader_task.delay')
    def test_create_submission_invalid_language_should_return_400(self, mock_delay):
        mock_delay.return_value = 1
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Elixir'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)
        # If this test ever fails, this app must be going places
        self.assertEqual(response.data['error'], "The language Elixir is not supported!")

    @patch('challenges.views.run_grader_task.delay')
    def test_create_two_submissions_in_10_seconds_second_should_not_work(self, mock_delay):
        mock_delay.return_value = 1
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

    @patch('challenges.views.run_grader_task.delay')
    @patch('challenges.views.MIN_SUBMISSION_INTERVAL_SECONDS', 0.1)
    def test_create_two_submissions_MIN_SUBMISSION_INTERVAL_seconds_apart_should_not_work(self, mock_delay):
        """ Our request should be denied if we create two submissions in the MIN_SUBMISSION_INTERVAL
                (to avoid flooding)
        """
        mock_delay.return_value = 1
        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 2)

        time.sleep(1)

        response = self.client.post('/challenges/{}/submissions/new'.format(self.challenge.id),
                                    data={'code': 'print("Hello World")', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.count(), 3)

    @patch('challenges.views.run_grader_task.delay')
    def test_create_submission_invalid_challenge_should_return_400(self, mock_delay):
        mock_delay.return_value = 1
        response = self.client.post('/challenges/111/submissions/new',
                                    data={'code': 'heyfriendheytherehowareyou', 'language': 'Python'},
                                    HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)

    def test_get_top_submissions(self):
        better_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="",
                                       result_score=50)
        # Second user with submissions
        _s_user = User.objects.create(username='Seocnd user', password='123', email='EC@abv.bg', score=123, role=self.base_role)
        _submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=_s_user, code="", result_score=50)
        top_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=_s_user, code="", result_score=51)

        # Should return the two submissions, (both users' best submissions) ordered by score descending
        response = self.client.get(f'/challenges/{self.challenge.id}/submissions/top', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, LimitedSubmissionSerializer([top_submission, better_submission], many=True).data)

    def test_get_top_submissions_invalid_id(self):
        response = self.client.get('/challenges/33/submissions/top', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], f'Invalid challenge id 33!')

    @patch('challenges.models.Submission.fetch_top_submissions_for_challenge')
    def test_get_top_submissions_calls_Submission_method(self, mock_top_submissions):
        """ Should call the submissions method for fetching the top challenges """
        self.client.get(f'/challenges/{self.challenge.id}/submissions/top', HTTP_AUTHORIZATION=self.auth_token)
        mock_top_submissions.assert_called_once_with(challenge_id=str(self.challenge.id))

    def test_get_self_top_submission(self):
        """ Should return the user's top submission """
        new_user = User.objects.create(username='1223', password='123', email='12223@abv.bg', score=123, role=self.base_role)
        new_auth_token = 'Token {}'.format(new_user.auth_token.key)
        submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=new_user,
                                                code="", result_score=5, pending=False)
        top_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=new_user,
                                                    code="", result_score=6, pending=False)
        sec_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=new_user,
                                                    code="", result_score=5, pending=False)

        response = self.client.get(f'/challenges/{self.challenge.id}/submissions/selfTop', HTTP_AUTHORIZATION=new_auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, LimitedSubmissionSerializer(top_submission).data)

    def test_get_self_top_submission_no_submission(self):
        """ Should return 404 """
        new_user = User.objects.create(username='1223', password='123', email='12223@abv.bg', score=123, role=self.base_role)
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


class LatestSubmissionsViewTest(TestCase, TestHelperMixin):
    def setUp(self):
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.python_language = Language.objects.create(name="Python")

        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.c1 = ChallengeFactory(category=self.sub_cat)
        self.c2 = ChallengeFactory(category=self.sub_cat)
        self.c3 = ChallengeFactory(category=self.sub_cat)

        self.create_user_and_auth_token()

    def test_get_latest_challenge_submissions_from_user(self):
        """ The get_latest_submissions view should return 3 the latest submissions by the user distinct by their challenges"""
        s1 = SubmissionFactory(author=self.auth_user, challenge=self.c1, pending=False)
        s2 = SubmissionFactory(author=self.auth_user, challenge=self.c2, pending=False)
        s3 = SubmissionFactory(author=self.auth_user, challenge=self.c3, pending=False)
        s4 = SubmissionFactory(author=self.auth_user, challenge=self.c2, pending=False)

        # view queries for the best submission
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

    def test_get_latest_challenge_submissions_from_user_hardcore_test(self):
        """
        As this gets the latest submissions by the user distinct by their challenges, at max 10, lets test it out more seriously
        :return:
        """
        # create 30 challenges
        for i in range(1, 31):
            exec(f'self.c{i} = ChallengeFactory(category=self.sub_cat)')
        # create 90 submissions, 3 for each challenge
        submission_id = 1
        for i in range(1, 31):
            exec(f'self.s{submission_id} = SubmissionFactory(author=self.auth_user, challenge=self.c{i}, pending=False)')
            exec(f'self.s{submission_id+1} = SubmissionFactory(author=self.auth_user, challenge=self.c{i}, pending=False)')
            exec(f'self.s{submission_id+2} = SubmissionFactory(author=self.auth_user, challenge=self.c{i}, pending=False)')
            submission_id += 3

        # This should return the 20-30 challenges in reverse order
        expected_data = LimitedChallengeSerializer(
            [self.c30, self.c29, self.c28, self.c27, self.c26, self.c25, self.c24, self.c23, self.c22, self.c21],
            many=True, context={'request': MagicMock(user=self.auth_user)}).data
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


class SubmissionVoteModelTest(TestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    def test_upvote_creation_creates_notification(self):
        other_user = UserFactory()
        SubmissionVote.objects.create(author=other_user, submission=self.submission, is_upvote=True, to_notify=True)
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.recipient, self.submission.author)
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION)

    def test_upvote_creation_doesnt_create_notification_by_default(self):
        other_user = UserFactory()
        SubmissionVote.objects.create(author=other_user, submission=self.submission, is_upvote=True, to_notify=False)
        self.assertEqual(Notification.objects.count(), 0)

    def test_upvote_creation_doesnt_create_notification_if_submission_author_upvotes(self):
        SubmissionVote.objects.create(author=self.auth_user, submission=self.submission, is_upvote=True, to_notify=True)
        self.assertEqual(Notification.objects.count(), 0)

    def test_downvote_creation_doesnt_create_notification(self):
        other_user = UserFactory()
        SubmissionVote.objects.create(author=other_user, submission=self.submission, is_upvote=False, to_notify=True)
        self.assertEqual(Notification.objects.count(), 0)

    def test_cannot_save_blank(self):
        s = SubmissionVote(author=self.auth_user)
        with self.assertRaises(Exception):
            s.full_clean()

    def test_cannot_save_duplicate_vote(self):
        SubmissionVote.objects.create(author=self.auth_user, submission=self.submission, is_upvote=True)
        s2 = SubmissionVote(author=self.auth_user, submission=self.submission, is_upvote=False)
        with self.assertRaises(IntegrityError):
            s2.save()


class SubmissionVoteViewTest(APITestCase, TestHelperMixin):
    def setUp(self):
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.python_language = Language.objects.create(name="Python")

        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.c1 = ChallengeFactory(category=self.sub_cat)

        self.create_user_and_auth_token()
        submission_user = UserFactory()
        self.submission = Submission.objects.create(language=self.python_language, challenge=self.c1, author=submission_user,
                            code="")

    def test_cast_submission_vote_creates_vote(self):
        self.assertEqual(len(SubmissionVote.objects.all()), 0)
        response = self.client.post(f'/challenges/submissions/{self.submission.id}/vote', HTTP_AUTHORIZATION=self.auth_token, data={
            'is_upvote': True
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(SubmissionVote.objects.all()), 1)
        self.assertTrue(SubmissionVote.objects.all().first().is_upvote)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.get_votes_count(), (1, 0))
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.type, RECEIVE_SUBMISSION_UPVOTE_NOTIFICATION)
        self.assertEqual(notif.recipient, self.submission.author)

    def test_cast_submission_vote_modifies_upvote_to_downvote(self):
        SubmissionVote.objects.create(author_id=self.auth_user.id, submission_id=self.submission.id, is_upvote=True)
        self.assertEqual(len(SubmissionVote.objects.all()), 1)

        response = self.client.post(f'/challenges/submissions/{self.submission.id}/vote', HTTP_AUTHORIZATION=self.auth_token,
                                    data={
                                        'is_upvote': False
                                    })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(SubmissionVote.objects.all()), 1)
        self.assertFalse(SubmissionVote.objects.all().first().is_upvote)  # should have been modified

    def test_cast_submission_vote_doesnt_modify_upvote_when_voted_again(self):
        SubmissionVote.objects.create(author_id=self.auth_user.id,
                                                        submission_id=self.submission.id, is_upvote=True)
        self.assertEqual(len(SubmissionVote.objects.all()), 1)

        response = self.client.post(f'/challenges/submissions/{self.submission.id}/vote', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'is_upvote': True})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(SubmissionVote.objects.all()), 1)
        self.assertTrue(SubmissionVote.objects.all().first().is_upvote)  # should have been modified

    def test_cast_submission_vote_invalid_submission_id_returns_404(self):
        response = self.client.post(f'/challenges/submissions/111/vote', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'is_upvote': True})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'A submission with ID 111 does not exist!')

    def test_user_cannot_vote_on_his_own_submission(self):
        own_subm = Submission.objects.create(language=self.python_language, challenge=self.c1,
                                                    author=self.auth_user,
                                                    code="")

        response = self.client.post(f'/challenges/submissions/{own_subm.id}/vote', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'is_upvote': True})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'You cannot vote on your own submission!')

    def test_user_remove_own_submission_returns_400(self):
        own_subm = Submission.objects.create(language=self.python_language, challenge=self.c1,
                                                    author=self.auth_user,
                                                    code="")

        response = self.client.delete(f'/challenges/submissions/{own_subm.id}/removeVote', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'is_upvote': True})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'You cannot vote on your own submission!')

    def test_remove_submission_vote_invalid_submission_id_returns_404(self):
        response = self.client.delete(f'/challenges/submissions/111/removeVote', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'A submission with ID 111 does not exist!')

    def test_remove_submission_vote_no_vote_returns_404(self):
        response = self.client.delete(f'/challenges/submissions/{self.submission.id}/removeVote', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], f'The user has not voted for submission with ID {self.submission.id}')

    def test_remove_submission_vote_removes_vote(self):
        SubmissionVote.objects.create(author_id=self.auth_user.id,
                                      submission_id=self.submission.id, is_upvote=True)
        self.assertEqual(len(SubmissionVote.objects.all()), 1)

        response = self.client.delete(f'/challenges/submissions/{self.submission.id}/removeVote', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(SubmissionVote.objects.all()), 0)


class SubmissionCommentViewTest(APITestCase, TestHelperMixin):
    def setUp(self):
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.python_language = Language.objects.create(name="Python")

        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.c1 = ChallengeFactory(category=self.sub_cat)

        self.create_user_and_auth_token()
        submission_user = UserFactory()
        self.submission = Submission.objects.create(language=self.python_language, challenge=self.c1, author=submission_user,
                                                    code="", pending=False)

    # Comment Create Tests

    def test_create_comment(self):
        # create a solved submission for auth_user to give him access
        Submission.objects.create(language=self.python_language, challenge=self.c1, author=self.auth_user,
                                  result_score=self.c1.score, pending=False, code="")

        us = UserFactory()
        Submission.objects.create(language=self.python_language, challenge=self.c1,
                                  author=us, code="", result_score=self.c1.score, pending=False)

        response = self.client.post(f'/challenges/{self.c1.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.submission.comments.count(), 1)
        self.assertEqual(self.submission.comments.first().author, self.auth_user)
        self.assertEqual(self.submission.comments.first().content, 'Hello World')
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().type, RECEIVE_SUBMISSION_COMMENT_NOTIFICATION)

    def test_user_cannot_comment_on_submission_he_has_not_solved(self):
        """ The user cannot comment on a submission he does not have access to """
        # incomplete submission
        Submission.objects.create(language=self.python_language, challenge=self.c1,
                                  author=self.auth_user, code="", result_score=self.c1.score-1)
        response = self.client.post(f'/challenges/{self.c1.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.submission.comments.count(), 0)

    def test_view_calls_add_comment(self):
        add_comment_mock = MagicMock()
        submission_mock = MagicMock(add_comment=add_comment_mock)
        SubmissionCommentCreateView().add_comment(submission=submission_mock, author=self.auth_user,
                                                  content='Wtf is UP :)')

        add_comment_mock.assert_called_once_with(author=self.auth_user, content='Wtf is UP :)', to_notify=True)

    def test_author_can_comment_on_own_submission_even_if_not_solved(self):
        user_submission = Submission.objects.create(language=self.python_language, challenge=self.c1,
                                                    author=self.auth_user, code="", result_score=0)
        response = self.client.post(f'/challenges/{self.c1.id}/submissions/{user_submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(user_submission.comments.count(), 1)
        self.assertEqual(user_submission.comments.first().author, self.auth_user)
        self.assertEqual(user_submission.comments.first().content, 'Hello World')

    def test_returns_400_in_non_matching_challenge_submission(self):
        c2 = ChallengeFactory(category=self.sub_cat)

        response = self.client.post(f'/challenges/{c2.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})

        self.assertEqual(response.status_code, 400)

    def test_returns_400_in_non_matching_challenge_submission_2(self):
        c2 = ChallengeFactory(category=self.sub_cat)
        c2_submission = Submission.objects.create(language=self.python_language, challenge=c2,
                                                  author=self.auth_user, code="", pending=False)

        response = self.client.post(f'/challenges/{self.c1.id}/submissions/{c2_submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})

        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_comment_is_not_str(self):
        # create a solved submission for auth_user to give him access
        Submission.objects.create(language=self.python_language, challenge=self.c1,
                                  author=self.auth_user, code="", result_score=self.c1.score, pending=False)
        response = self.client.post(f'/challenges/{self.c1.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 123456}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_comment_is_too_short(self):
        # create a solved submission for auth_user to give him access
        Submission.objects.create(language=self.python_language, challenge=self.c1,
                                  author=self.auth_user, code="", result_score=self.c1.score, pending=False)
        response = self.client.post(f'/challenges/{self.c1.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'wh'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_comment_is_too_long(self):
        # create a solved submission for auth_user to give him access
        Submission.objects.create(language=self.python_language, challenge=self.c1,
                                  author=self.auth_user, code="", result_score=self.c1.score, pending=False)
        response = self.client.post(f'/challenges/{self.c1.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'wh'*500}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_non_existent_challenge_returns_404(self):
        # create a solved submission for auth_user to give him access
        Submission.objects.create(language=self.python_language, challenge=self.c1,
                                  author=self.auth_user, code="", result_score=self.c1.score, pending=False)
        response = self.client.post(f'/challenges/1342/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'yoyoyoyo'}, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_non_existent_submission_returns_404(self):
        # create a solved submission for auth_user to give him access
        Submission.objects.create(language=self.python_language, challenge=self.c1,
                                  author=self.auth_user, code="", result_score=self.c1.score, pending=False)
        response = self.client.post(f'/challenges/{self.c1.id}/submissions/1234/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'what'}, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_requires_authentication(self):
        response = self.client.post(f'/challenges/{self.c1.id}/submissions/1234/comments',
                                    data={'content': 'what'}, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    # Comment Create Tests
