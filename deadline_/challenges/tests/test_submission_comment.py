from rest_framework.test import APITestCase

from challenges.models import SubmissionComment, Submission
from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import UserFactory


class SubmissionCommentCreateReplyView(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()
        self.second_user = UserFactory(); self.second_user.save()
        self.second_token = 'Token {}'.format(self.second_user.auth_token.key)

        self.comment = SubmissionComment.objects.create(submission=self.submission, author=self.second_user, content='Hello, my name is boris')

    def test_can_create_reply(self):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.comment.replies.count(), 1)
        self.assertEqual(self.comment.replies.first().content, 'When the night call ye')
        self.assertEqual(self.comment.replies.first().author, self.auth_user)

    def test_ignores_forbidden_fields(self):
        """ Should not be able to edit parent_id, submission_id or author_id"""
        second_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                      author=self.second_user, code="")
        new_comment = SubmissionComment.objects.create(submission=second_submission, author=self.second_user, content='Hello, my name is boris')
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye',
                                          'submission': second_submission.id,
                                          'submission_id': second_submission.id,
                                          'author': self.second_user.id,
                                          'author_id': self.second_user.id,
                                          'parent': new_comment.id,
                                          'parent_id': new_comment.id})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.comment.replies.count(), 1)
        reply = self.comment.replies.first()
        self.assertEqual(reply.author, self.auth_user)
        self.assertEqual(reply.submission, self.submission)

    def test_returns_400_if_user_has_not_solved_challenge(self):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.second_token,
                                    data={'content': 'When the night call ye'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.comment.replies.count(), 0)

    def test_is_created_if_user_has_solved_challenge(self):
        # Create a solved Submission
        Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                  author=self.second_user, code="",
                                  result_score=self.challenge.score, pending=False)
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.second_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.comment.replies.count(), 1)
        self.assertEqual(self.comment.replies.first().content, 'When the night call ye')
        self.assertEqual(self.comment.replies.first().author, self.second_user)

    def test_returns_404_if_invalid_challenge(self):
        response = self.client.post(f'/challenges/111/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_invalid_submission(self):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/111/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 404)

    def test_returns_404_if_invalid_comment(self):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/111',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 404)

    def test_invalid_challenge_submission_relation_returns_400(self):
        second_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                      author=self.second_user, code="")
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{second_submission.id}/comments/{self.comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.comment.replies.count(), 0)

    def test_invalid_submission_comment_relation_returns_400(self):
        second_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                      author=self.second_user, code="")
        new_comment = SubmissionComment.objects.create(submission=second_submission, author=self.second_user, content='Hello, my name is boris')
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{new_comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'When the night call ye'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(new_comment.replies.count(), 0)

    def test_requires_authentication(self):
        response = self.client.post(f'/challenges/{self.challenge.id}/submissions/{self.submission.id}/comments/{self.comment.id}',
                                    data={'content': 'When the night call ye'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.comment.replies.count(), 0)
