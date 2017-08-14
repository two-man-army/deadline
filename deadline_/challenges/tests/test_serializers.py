from collections import OrderedDict
from unittest.mock import MagicMock

from django.test import TestCase
from rest_framework.renderers import JSONRenderer

from accounts.serializers import UserSerializer
from challenges.serializers import LimitedSubmissionSerializer, SubmissionSerializer, SubmissionCommentSerializer, \
    ChallengeCommentSerializer, ChallengeSerializer, ChallengeDescriptionSerializer
from challenges.models import Submission, SubmissionVote, ChallengeDescription, MainCategory, SubCategory, Language, \
    Challenge, Proficiency, SubmissionComment, ChallengeComment
from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import ChallengeDescFactory, UserFactory
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
        expected_data = {'id': s.id, 'challenge': s.challenge.id, 'author': s.author.username, 'code': s.code,
                         'result_score': s.result_score, 'pending': s.pending,
                         'created_at': s.created_at.isoformat()[:-6] + 'Z', 'compiled': s.compiled,
                         'compile_error_message': s.compile_error_message, 'language': s.language.name,
                         'timed_out': s.timed_out, 'comments': [], 'user_has_voted': True, 'user_has_upvoted': False,
                         'upvote_count': 0, 'downvote_count': 1}

        self.assertEqual(expected_data, serializer.data)

    def test_serializes_comments_and_sorts_by_order_date(self):
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user, code="DMV")
        s.add_comment(author=self.auth_user, content='1Hello :)')
        s.add_comment(author=self.auth_user, content='Hello 2')
        serializer = SubmissionSerializer(s, context={'request': MagicMock(user=self.auth_user)})
        comments = SubmissionComment.objects.all().order_by('-created_at')
        expected_data = SubmissionCommentSerializer(many=True, instance=comments).data

        self.assertEqual(expected_data, serializer.data['comments'])


class SubmissionCommentSerializerTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    def test_serialization(self):
        subm_comment = SubmissionComment.objects.create(submission=self.submission,
                                                        author=self.auth_user, content="Hello World")

        expected_data = {'id': subm_comment.id, 'author': subm_comment.author.username, 'content': subm_comment.content}
        received_data = SubmissionCommentSerializer(instance=subm_comment).data

        self.assertEqual(expected_data, received_data)


class ChallengeSerializerTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.sample_desc = ChallengeDescFactory()
        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        self.rust_lang = Language.objects.create(name='Rust')
        self.python_lang = Language.objects.create(name='Python')
        self.c_lang = Language.objects.create(name='C')

    def test_serialization(self):
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat,
                                     description=self.sample_desc)
        c.supported_languages.add(*[self.rust_lang, self.c_lang, self.python_lang])

        expected_description_data = ChallengeDescriptionSerializer(instance=self.sample_desc).data
        expected_data = {
            'id': c.id, 'name': c.name, 'difficulty': c.difficulty, 'score': c.score,
            'description': expected_description_data, 'test_case_count': c.test_case_count,
            'category': c.category.name, 'supported_languages': [lang.name for lang in c.supported_languages.all()],
            'comments': []
        }

        received_data = ChallengeSerializer(c).data
        self.assertEqual(received_data, expected_data)

    def test_serializes_comments_and_sorts_by_creation_date(self):
        c = Challenge.objects.create(name='Hello', difficulty=5, score=10, test_case_count=5, category=self.sub_cat,
                                     description=self.sample_desc)
        c.add_comment(author=self.auth_user, content='1Hello :)')
        c.add_comment(author=self.auth_user, content='Hello 2')
        serializer = ChallengeSerializer(c)
        comments = ChallengeComment.objects.all().order_by('-created_at')

        expected_data = ChallengeCommentSerializer(many=True, instance=comments).data
        self.assertEqual(expected_data, serializer.data['comments'])


class ChallengeCommentSerializerTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    def test_serialization(self):
        challenge_comment = ChallengeComment.objects.create(challenge=self.challenge,
                                                            author=self.auth_user, content='Hello World')
        author_data = OrderedDict(UserSerializer(self.auth_user).data)
        expected_data = {'id': challenge_comment.id, 'author': author_data, 'content': challenge_comment.content, 'replies': []}
        received_data = ChallengeCommentSerializer(instance=challenge_comment).data

        self.assertEqual(expected_data, received_data)

    def test_nested_serialization(self):
        author_data = OrderedDict(UserSerializer(self.auth_user).data)

        challenge_comment = ChallengeComment.objects.create(challenge=self.challenge,
                                                            author=self.auth_user, content='Hello World')
        first_reply = challenge_comment.add_reply(author=self.auth_user, content='Ill Mind')
        first_reply_reply = first_reply.add_reply(author=self.auth_user, content='lift weights')
        first_reply_reply_reply = first_reply_reply.add_reply(author=self.auth_user, content='scary fella')
        second_reply = challenge_comment.add_reply(author=self.auth_user, content='grind disorder')
        # this also asserts that replies are sorted by creation date descending
        expected_data = {
            'id': challenge_comment.id,
            'content': challenge_comment.content,
            'author': author_data,
            'replies': [
                {
                    'id': second_reply.id,
                    'content': second_reply.content,
                    'author': author_data,
                    'replies': []
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
                                    'replies': []
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        self.assertEqual(expected_data, ChallengeCommentSerializer(challenge_comment).data)

    def test_deserialize_ignores_read_only_fields(self):
        new_user = UserFactory(); new_user.save()
        desc = ChallengeDescFactory()
        new_c = Challenge.objects.create(name='Stay Callin', difficulty=5, score=10, description=desc,
                                                  test_case_count=2, category=self.sub_cat)
        challenge_comment = ChallengeComment.objects.create(challenge=self.challenge,
                                                            author=self.auth_user, content='Hello World')
        ser = ChallengeCommentSerializer(data={'id': 2014, 'content': 'change', 'author_id': new_user.id, 'parent_id': challenge_comment.id,
                                               'challenge_id': new_c.id})
        self.assertTrue(ser.is_valid())
        new_comment = ser.save(author=self.auth_user, challenge=self.challenge)

        self.assertNotEqual(new_comment.id, 2014)
        self.assertEqual(new_comment.author, self.auth_user)
        self.assertIsNone(new_comment.parent)
        self.assertEqual(new_comment.content, 'change')
        self.assertEqual(new_comment.challenge, self.challenge)
