from unittest.mock import patch, MagicMock

from rest_framework.test import APITestCase

from accounts.models import User
from challenges.tests.base import TestHelperMixin
from social.constants import NW_ITEM_TEXT_POST, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION, \
    RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION
from social.models import NewsfeedItem, NewsfeedItemComment, Notification
from social.views import NewsfeedItemCommentReplyCreateView


class NewsfeedCommentCreateViewTests(APITestCase, TestHelperMixin):
    """
    Should create a comment for a NewsfeedItem
    """
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.nw_item = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

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
        # Should also create a notification
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().type, RECEIVE_NW_ITEM_COMMENT_NOTIFICATION)

    def test_uneditable_fields_should_not_affect_creation(self):
        # fields like author and newsfeed item should be set by the view
        #   in regards to who issued the request and what nw_item we picked in the URL
        new_nw_item = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
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
        self.nw_item = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
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
        # Should also create a notification
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION)

    def test_read_only_fields_should_not_affect_creation(self):
        new_nw_item = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
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
        # Should also create a notification
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().type, RECEIVE_NW_ITEM_COMMENT_REPLY_NOTIFICATION)

    @patch('social.views.NewsfeedItemCommentReplyCreateView.create_reply')
    def test_view_calls_add_reply(self, mock_cr_repl):
        self.client.post(f'/social/feed/items/{self.nw_item.id}/comments/{self.nw_comment.id}',
                         HTTP_AUTHORIZATION=self.auth_token,
                         data={'content': 'No rest for the wicked'})
        mock_cr_repl.assert_called_once_with(author=self.auth_user, nw_item_comment=self.nw_comment,
                                             content='No rest for the wicked')

    def test_create_reply_calls_add_reply(self):
        add_reply_mock = MagicMock()
        comment_mock = MagicMock(add_reply=add_reply_mock)
        NewsfeedItemCommentReplyCreateView().create_reply(author=self.auth_user, nw_item_comment=comment_mock,
                                                          content='No rest for the wicked')

        add_reply_mock.assert_called_once_with(to_notify=True, content='No rest for the wicked', author=self.auth_user)

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
        new_nw_item = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
        new_nw_comment = NewsfeedItemComment.objects.create(newsfeed_item=new_nw_item, author=self.user2, content='Tanktank')
        response = self.client.post(f'/social/feed/items/{self.nw_item.id}/comments/{new_nw_comment.id}',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'content': 'No rest for the wicked'})
        self.assertEqual(response.status_code, 400)
