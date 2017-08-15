from django.test import TestCase
from rest_framework.test import APITestCase

from challenges.tests.base import TestHelperMixin


class ChallengeCommentModelTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    def test_add_comment(self):
        new_comment = self.challenge.add_comment(author=self.auth_user, content='Frozen')
        self.assertEqual(self.challenge.comments.count(), 1)
        self.assertEqual(self.challenge.comments.first(), new_comment)
        self.assertEqual(new_comment.replies.count(), 0)
        self.assertEqual(new_comment.author, self.auth_user)
        self.assertEqual(new_comment.content, 'Frozen')
        self.assertIsNone(new_comment.parent)
        self.assertEqual(new_comment.replies.count(), 0)

    def test_add_reply(self):
        new_comment = self.challenge.add_comment(author=self.auth_user, content='Frozen')
        new_reply = new_comment.add_reply(author=self.auth_user, content='Stone')
        self.assertEqual(new_reply.replies.count(), 0)
        self.assertEqual(new_comment.replies.count(), 1)
        self.assertEqual(new_comment.replies.first(), new_reply)
        self.assertEqual(new_reply.content, 'Stone')
        self.assertEqual(new_reply.parent, new_comment)
        self.assertEqual(new_reply.author, self.auth_user)

    def test_get_absolute_url(self):
        new_comment = self.challenge.add_comment(author=self.auth_user, content='Frozen')
        expected_url = f'/challenges/{self.challenge.id}/comments/{new_comment.id}'
        self.assertEqual(new_comment.get_absolute_url(), expected_url)


class ChallengeCommentViewTest(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()
        self.c1 = self.challenge

    # Comment Create Tests
    def test_create_comment(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.c1.comments.count(), 1)
        self.assertEqual(self.c1.comments.first().author, self.auth_user)
        self.assertEqual(self.c1.comments.first().content, 'Hello World')

    def test_returns_400_if_comment_is_not_str(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 123456}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_comment_is_too_short(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'wh'})
        self.assertEqual(response.status_code, 400)

    def test_returns_400_if_comment_is_too_long(self):
        response = self.client.post(f'/challenges/{self.c1.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'*500})
        self.assertEqual(response.status_code, 400)

    def test_non_existent_challenge_returns_404(self):
        response = self.client.post(f'/challenges/111/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'Hello World'})
        self.assertEqual(response.status_code, 404)

    def test_requires_authentication(self):
        response = self.client.post(f'/challenges/111/comments',
                                    data={'content': 'Hello World'})
        self.assertEqual(response.status_code, 401)

        # Comment Create Tests
