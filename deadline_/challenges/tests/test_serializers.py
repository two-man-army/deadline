from unittest.mock import MagicMock

from django.test import TestCase
from rest_framework.renderers import JSONRenderer

from challenges.serializers import LimitedSubmissionSerializer, SubmissionSerializer
from challenges.models import Submission, SubmissionVote, ChallengeDescription, MainCategory, SubCategory, Language, Challenge, Proficiency
from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import ChallengeDescFactory
from accounts.models import User


class LimitedSubmissionSerializerTests(TestCase, TestHelperMixin):
    """ The LimitedSubmissionSerializer should attach four fields to the deserialized content
        - user_has_voted - Boolean indicating if the user has voted at all for this
        - user_has_upvoted - Boolean indicating if the user has upvoted the submission (user_has_voted must be true)
        - upvote_count - int showing the amount of upvotes this submission has
        - downvote_count - int showing the amount of downvotes this submission has
    """
    def setUp(self):
        self.base_set_up()

    def test_serialize_attaches_expected_variables(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                                code="hust", result_score=10, pending=False)
        sv = SubmissionVote.objects.create(is_upvote=True, submission_id=submission.id, author_id=self.auth_user.id); sv.save()

        received_submission = LimitedSubmissionSerializer(submission, context={'request': req_mock}).data

        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], True)
        self.assertEqual(received_submission['upvote_count'], 1)
        self.assertEqual(received_submission['downvote_count'], 0)

    def test_serialize_correctly_sets_user_has_upvoted(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                code="hust", result_score=10, pending=False)
        sv = SubmissionVote.objects.create(is_upvote=False, submission_id=submission.id, author_id=self.auth_user.id);

        received_submission = LimitedSubmissionSerializer(submission, context={'request': req_mock}).data
        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], False)
        self.assertEqual(received_submission['upvote_count'], 0)
        self.assertEqual(received_submission['downvote_count'], 1)

    def test_limited_serialization_should_not_serialize_code(self):

        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                      code="BAGDAD")
        serializer = LimitedSubmissionSerializer(s)
        created_at_date = s.created_at.isoformat()[:-6] + 'Z'
        expected_json = (f'{{"id":{s.id},"challenge":{self.challenge.id},"author":"{self.auth_user.username}",'
                         f'"result_score":0,"pending":true,"created_at":"{created_at_date}",'
                         f'"compiled":true,"compile_error_message":"","language":"Python","timed_out":false,'
                         f'"user_has_voted":false,"user_has_upvoted":false,"upvote_count":0,"downvote_count":0}}')
        content = JSONRenderer().render(serializer.data)
        self.assertEqual(content.decode('utf-8').replace('\\n', '\n'), expected_json)


class SubmissionSerializerTests(TestCase, TestHelperMixin):
    """ The SubmissionSerializer should attach four fields to the deserialized content
        - user_has_voted - Boolean indicating if the user has voted at all for this
        - user_has_upvoted - Boolean indicating if the user has upvoted the submission (user_has_voted must be true)
        - upvote_count - int showing the amount of upvotes this submission has
        - downvote_count - int showing the amount of downvotes this submission has
    """
    def setUp(self):
        self.base_set_up()

    def test_serialize_attaches_expected_variables(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                               code="hoola", result_score=10, pending=False)
        SubmissionVote.objects.create(is_upvote=True, submission_id=submission.id, author_id=self.auth_user.id)

        received_submission = SubmissionSerializer(submission, context={'request': req_mock}).data

        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], True)
        self.assertEqual(received_submission['upvote_count'], 1)
        self.assertEqual(received_submission['downvote_count'], 0)

    def test_serialize_correctly_sets_user_has_upvoted(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                code="", result_score=10, pending=False)
        sv = SubmissionVote.objects.create(is_upvote=False, submission_id=submission.id, author_id=self.auth_user.id);

        received_submission = SubmissionSerializer(submission, context={'request': req_mock}).data
        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], False)
        self.assertEqual(received_submission['upvote_count'], 0)
        self.assertEqual(received_submission['downvote_count'], 1)

    def test_serialization(self):
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="DMV")
        sv = SubmissionVote.objects.create(submission_id=s.id, author_id=self.auth_user.id, is_upvote=False); sv.save()
        serializer = SubmissionSerializer(s, context={'request': MagicMock(user=self.auth_user)})
        created_at_date = s.created_at.isoformat()[:-6] + 'Z'
        expected_json = (f'{{"id":{s.id},"challenge":{self.challenge.id},"author":"{self.auth_user.username}",'
                         f'"code":"{"DMV"}","result_score":0,"pending":true,"created_at":"{created_at_date}",'
                         f'"compiled":true,"compile_error_message":"","language":"Python","timed_out":false,'
                         f'"upvote_count":0,"downvote_count":1,"user_has_voted":true,"user_has_upvoted":false}}')
        content = JSONRenderer().render(serializer.data)
        self.assertEqual(content.decode('utf-8').replace('\\n', '\n'), expected_json)