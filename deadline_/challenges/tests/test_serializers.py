from django.test import TestCase
from unittest.mock import MagicMock
from challenges.serializers import LimitedSubmissionSerializer, SubmissionSerializer
from challenges.models import Submission, SubmissionVote, ChallengeDescription, MainCategory, SubCategory, Language, Challenge
from accounts.models import User


class TestLimitedSubmissionSerializer(TestCase):
    """ The LimitedSubmissionSerializer should attach four fields to the deserialized content
        - user_has_voted - Boolean indicating if the user has voted at all for this
        - user_has_upvoted - Boolean indicating if the user has upvoted the submission (user_has_voted must be true)
        - upvote_count - int showing the amount of upvotes this submission has
        - downvote_count - int showing the amount of downvotes this submission has
    """
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.python_language = Language.objects.create(name="Python"); self.python_language.save()
        self.sample_desc.save()
        challenge_cat = MainCategory.objects.create(name='Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', difficulty=5, score=10, description=self.sample_desc,
                                   test_file_name='hello_tests',
                                   test_case_count=3, category=self.sub_cat)
        self.challenge.save()
        self.challenge.supported_languages.add(self.python_language)
        self.challenge_name = self.challenge.name
        self.auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        self.auth_user.save()
        self.sample_code = "a"
        self.submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                     code=self.sample_code, result_score=10, pending=0)
        self.submission.save()

    def test_serialize_attaches_expected_variables(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                code=self.sample_code, result_score=10, pending=0)
        submission.save()
        sv = SubmissionVote(is_upvote=True, submission_id=submission.id, author_id=self.auth_user.id); sv.save()
        sv.save()

        received_submission = LimitedSubmissionSerializer(submission, context={'request': req_mock}).data

        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], True)
        self.assertEqual(received_submission['upvote_count'], 1)
        self.assertEqual(received_submission['downvote_count'], 0)

    def test_serialize_correctly_sets_user_has_upvoted(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                code=self.sample_code, result_score=10, pending=0)
        submission.save()
        sv = SubmissionVote(is_upvote=False, submission_id=submission.id, author_id=self.auth_user.id);
        sv.save()

        received_submission = LimitedSubmissionSerializer(submission, context={'request': req_mock}).data
        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], False)
        self.assertEqual(received_submission['upvote_count'], 0)
        self.assertEqual(received_submission['downvote_count'], 1)


class TestSubmissionSerializer(TestCase):
    """ The SubmissionSerializer should attach four fields to the deserialized content
        - user_has_voted - Boolean indicating if the user has voted at all for this
        - user_has_upvoted - Boolean indicating if the user has upvoted the submission (user_has_voted must be true)
        - upvote_count - int showing the amount of upvotes this submission has
        - downvote_count - int showing the amount of downvotes this submission has
    """
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.python_language = Language.objects.create(name="Python"); self.python_language.save()
        self.sample_desc.save()
        challenge_cat = MainCategory.objects.create(name='Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        self.challenge = Challenge(name='Hello', difficulty=5, score=10, description=self.sample_desc,
                                   test_file_name='hello_tests',
                                   test_case_count=3, category=self.sub_cat)
        self.challenge.save()
        self.challenge.supported_languages.add(self.python_language)
        self.challenge_name = self.challenge.name
        self.auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        self.auth_user.save()
        self.sample_code = "a"
        self.submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                     code=self.sample_code, result_score=10, pending=0)
        self.submission.save()

    def test_serialize_attaches_expected_variables(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                code=self.sample_code, result_score=10, pending=0)
        submission.save()
        sv = SubmissionVote(is_upvote=True, submission_id=submission.id, author_id=self.auth_user.id); sv.save()
        sv.save()

        received_submission = SubmissionSerializer(submission, context={'request': req_mock}).data

        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], True)
        self.assertEqual(received_submission['upvote_count'], 1)
        self.assertEqual(received_submission['downvote_count'], 0)

    def test_serialize_correctly_sets_user_has_upvoted(self):
        req_mock = MagicMock(user=self.auth_user)
        submission = Submission(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                code=self.sample_code, result_score=10, pending=0)
        submission.save()
        sv = SubmissionVote(is_upvote=False, submission_id=submission.id, author_id=self.auth_user.id);
        sv.save()

        received_submission = SubmissionSerializer(submission, context={'request': req_mock}).data
        self.assertEqual(received_submission['user_has_voted'], True)
        self.assertEqual(received_submission['user_has_upvoted'], False)
        self.assertEqual(received_submission['upvote_count'], 0)
        self.assertEqual(received_submission['downvote_count'], 1)