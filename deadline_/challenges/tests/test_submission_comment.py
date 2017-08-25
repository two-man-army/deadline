from unittest.mock import patch

from rest_framework.test import APITestCase

from challenges.models import SubmissionComment, Submission
from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import UserFactory, ChallengeFactory


@patch('challenges.models.Submission.add_comment')
class SubmissionCommentCreateView(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()
        self.second_user = UserFactory(); self.second_user.save()
        self.second_token = 'Token {}'.format(self.second_user.auth_token.key)

    def test_can_comment_if_fully_solved(self, mock_add_comment):
        self.submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                    author=self.second_user, code="", result_score=self.challenge.score,
                                                    pending=False)
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.second_token, data={'content': 'Nice man!'})

        self.assertEqual(response.status_code, 201)
        mock_add_comment.assert_called_once_with(author=self.second_user, content='Nice man!', to_notify=True)

    def test_can_comment_if_author(self, mock_add_comment):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token, data={'content': 'Nice man!'})

        self.assertEqual(response.status_code, 201)
        mock_add_comment.assert_called_once_with(author=self.auth_user, content='Nice man!', to_notify=True)

    def test_cant_comment_if_short_content(self, mock_add_comment):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token, data={'content': 'n'})
        self.assertEqual(response.status_code, 400)
        mock_add_comment.assert_not_called()

    def test_cant_comment_if_long_content(self, mock_add_comment):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token, data={'content': 'N'*600})
        self.assertEqual(response.status_code, 400)
        mock_add_comment.assert_not_called()

    def test_cant_comment_if_user_hasnt_solved_challenge(self, mock_add_comment):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.second_token, data={'content': 'Nice man!'})
        self.assertEqual(response.status_code, 401)
        mock_add_comment.assert_not_called()

    def test_invalid_challenge_returns_404(self, mock_add_comment):
        response = self.client.post(f'/challenges/111/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.second_token, data={'content': 'Nice man!'})
        self.assertEqual(response.status_code, 404)
        mock_add_comment.assert_not_called()

    def test_invalid_submission_returns_404(self, mock_add_comment):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/111/comments',
                                    HTTP_AUTHORIZATION=self.second_token, data={'content': 'Nice man!'})
        self.assertEqual(response.status_code, 404)
        mock_add_comment.assert_not_called()

    def test_invalid_challenge_submission_relation_returns_400(self, mock_add_comment):
        response = self.client.post(f'/challenges/{ChallengeFactory().id}/submissions/{self.submission.id}/comments',
                                    HTTP_AUTHORIZATION=self.second_token, data={'content': 'Nice man!'})
        self.assertEqual(response.status_code, 400)
        mock_add_comment.assert_not_called()

    def test_requires_authentication(self, mock_add_comment):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments',
                                    data={'content': 'Nice man!'})
        self.assertEqual(response.status_code, 401)
        mock_add_comment.assert_not_called()


@patch('challenges.models.SubmissionComment.add_reply')
class SubmissionCommentCreateReplyView(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()
        self.second_user = UserFactory(); self.second_user.save()
        self.second_token = 'Token {}'.format(self.second_user.auth_token.key)

        self.comment = SubmissionComment.objects.create(submission=self.submission, author=self.second_user,
                                                        content='Hello, my name is boris')

    def test_can_create_reply(self, mock_add_reply):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 201)
        mock_add_reply.assert_called_once_with(author=self.auth_user, content='When the night call ye', to_notify=True)

    def test_is_created_if_user_has_solved_challenge(self, mock_add_reply):
        # Create a solved Submission
        Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                  author=self.second_user, code="",
                                  result_score=self.challenge.score, pending=False)
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.second_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 201)
        mock_add_reply.assert_called_once_with(author=self.second_user, content='When the night call ye', to_notify=True)

    def test_returns_401_if_user_has_not_solved_challenge(self, mock_add_reply):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.second_token,
                                    data={'content': 'When the night call ye'})
        self.assertEqual(response.status_code, 401)
        mock_add_reply.assert_not_called()

    def test_returns_404_if_invalid_challenge(self, mock_add_reply):
        response = self.client.post(f'/challenges/111/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 404)
        mock_add_reply.assert_not_called()

    def test_returns_404_if_invalid_submission(self, mock_add_reply):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/111/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 404)
        mock_add_reply.assert_not_called()

    def test_returns_404_if_invalid_comment(self, mock_add_reply):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/111',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 404)
        mock_add_reply.assert_not_called()

    def test_invalid_challenge_submission_relation_returns_400(self, mock_add_reply):
        second_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                      author=self.second_user, code="")
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{second_submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 400)
        mock_add_reply.assert_not_called()

    def test_invalid_submission_comment_relation_returns_400(self, mock_add_reply):
        second_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                      author=self.second_user, code="")
        new_comment = SubmissionComment.objects.create(submission=second_submission, author=self.second_user, content='Hello, my name is boris')
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{new_comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 400)
        mock_add_reply.assert_not_called()

    def test_requires_authentication(self, mock_add_reply):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    data={'content': 'When the night call ye'})
        self.assertEqual(response.status_code, 401)
        mock_add_reply.assert_not_called()
