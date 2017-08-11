from rest_framework.test import APITestCase

from accounts.models import User
from challenges.tests.base import TestHelperMixin
from social.models import NewsfeedItem, NewsfeedItemComment


class NewsfeedCommentCreateViewTests(APITestCase, TestHelperMixin):
    """
    Should create a comment for a NewsfeedItem
    """
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.nw_item = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})

    def test_comment_creation(self):
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'OK I WAS GONE FOR A MINUTE'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.nw_item.comments.count(), 1)
        nw_comment = self.nw_item.comments.first()
        self.assertEqual(nw_comment.author, self.auth_user)
        self.assertEqual(nw_comment.content, 'OK I WAS GONE FOR A MINUTE')
        self.assertIsNone(nw_comment.parent)

    def test_uneditable_fields_should_not_affect_creation(self):
        # fields like author and newsfeed item should be set by the view
        #   in regards to who issued the request and what nw_item we picked in the URL
        new_nw_item = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})
        new_nw_comment = NewsfeedItemComment.objects.create(newsfeed_item=new_nw_item, author=self.user2, content='Tanktank')
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'OK I WAS GONE FOR A MINUTE',
                                          'newsfeed_item': new_nw_item.id,
                                          'newsfeed_item_id': new_nw_item.id,
                                          'author': self.user2.id,
                                          'author_id': self.user2.id,
                                          'parent': new_nw_comment.id,
                                          'parent_id': new_nw_comment.id})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.nw_item.comments.count(), 1)
        nw_comment = self.nw_item.comments.first()
        self.assertEqual(nw_comment.author, self.auth_user)
        self.assertEqual(nw_comment.content, 'OK I WAS GONE FOR A MINUTE')
        self.assertEqual(nw_comment.newsfeed_item, self.nw_item)
        self.assertIsNone(nw_comment.parent)

    def test_requires_authentication(self):
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments',
                                    data={'content': 'OK I WAS GONE FOR A MINUTE'})

        self.assertEqual(response.status_code, 401)


class NewsfeedCommentReplyCreateViewTests(APITestCase, TestHelperMixin):
    """
    Should create a Reply to a NewsfeedItemComment
    """
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg',
                                         score=123, role=self.base_role)
        self.nw_item = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})
        self.nw_comment = NewsfeedItemComment.objects.create(author=self.user2, newsfeed_item=self.nw_item,
                                                             content='No song for the choir now')

    def test_should_create_reply(self):
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments/{self.nw_comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'No rest for the wicked'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.nw_comment.replies.count(), 1)
        reply = self.nw_comment.replies.first()
        self.assertEqual(reply.content, 'No rest for the wicked')
        self.assertEqual(reply.author, self.auth_user)
        self.assertEqual(reply.newsfeed_item, self.nw_item)
        self.assertEqual(reply.parent, self.nw_comment)

    def test_read_only_fields_should_not_affect_creation(self):
        new_nw_item = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})
        new_nw_comment = NewsfeedItemComment.objects.create(newsfeed_item=new_nw_item, author=self.user2, content='Tanktank')
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments/{self.nw_comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'OK I WAS GONE FOR A MINUTE',
                                          'newsfeed_item': new_nw_item.id,
                                          'newsfeed_item_id': new_nw_item.id,
                                          'author': self.user2.id,
                                          'author_id': self.user2.id,
                                          'parent': new_nw_comment.id,
                                          'parent_id': new_nw_comment.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.nw_comment.replies.count(), 1)
        reply = self.nw_comment.replies.first()
        self.assertEqual(reply.content, 'OK I WAS GONE FOR A MINUTE')
        self.assertEqual(reply.author, self.auth_user)
        self.assertEqual(reply.newsfeed_item, self.nw_item)
        self.assertEqual(reply.parent, self.nw_comment)

    def test_unauth_should_401(self):
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments/{self.nw_comment.id}',
                                    data={'content': 'No rest for the wicked'})
        self.assertEqual(response.status_code, 401)

    def test_invalid_nw_item_id_should_404(self):
        response = self.client.post(f'/social/feed/items/111/comments/{self.nw_comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'No rest for the wicked'})
        self.assertEqual(response.status_code, 404)

    def test_invalid_comment_id_should_404(self):
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments/111',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'No rest for the wicked'})
        self.assertEqual(response.status_code, 404)

    def test_invalid_nw_item_nw_comment_pair(self):
        new_nw_item = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})
        new_nw_comment = NewsfeedItemComment.objects.create(newsfeed_item=new_nw_item, author=self.user2, content='Tanktank')
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments/{new_nw_comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'No rest for the wicked'})
        self.assertEqual(response.status_code, 400)
