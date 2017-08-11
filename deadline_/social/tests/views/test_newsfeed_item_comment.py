from rest_framework.test import APITestCase

from accounts.models import User
from challenges.tests.base import TestHelperMixin
from social.models import NewsfeedItem, NewsfeedItemComment


class NewsfeedItemDetailViewTests(APITestCase, TestHelperMixin):
    """
    Should simply return information about a specific NewsfeedItem
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
