from rest_framework.test import APITestCase

from challenges.tests.base import TestHelperMixin
from social.models import NewsfeedItem


class TextPostCreateViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_create_post(self):
        self.client.post('/social/posts/', HTTP_AUTHORIZATION=self.auth_token,
                         data={
                             'content': 'Training hard',
                             'is_private': False
                         })
        self.assertEqual(NewsfeedItem.objects.count(), 1)
        nw_item = NewsfeedItem.objects.first()
        self.assertEqual(nw_item.content['content'], 'Training hard')
        self.assertEqual(nw_item.is_private, False)
        self.assertEqual(nw_item.author, self.auth_user)
        self.assertIsNotNone(nw_item.created_at)
        self.assertIsNotNone(nw_item.updated_at)

    def test_non_editable_fields_should_not_be_editable(self):
        """
        There are some fields that should not be changed regardless what request is given
        """
        self.client.post('/social/posts/', HTTP_AUTHORIZATION=self.auth_token,
                         data={
                             'content': 'Training hard',
                             'is_private': False,
                             'author': 20,
                             'author_id': 20,
                             'type': 'TANK_POST',
                             'created_at': 'Someday',
                             'updated_at': 'Some other day',
                             'comments': [
                                 {
                                     'author_id': 1,
                                     'content': 'yoyo'
                                 }
                             ]
                         })
        self.assertEqual(NewsfeedItem.objects.count(), 1)
        nw_item = NewsfeedItem.objects.first()
        self.assertEqual(nw_item.content['content'], 'Training hard')
        self.assertEqual(nw_item.is_private, False)
        self.assertEqual(nw_item.author, self.auth_user)
        self.assertEqual(nw_item.comments.count(), 0)
        self.assertIsNotNone(nw_item.created_at)
        self.assertNotEqual(nw_item.created_at, 'Someday')
        self.assertIsNotNone(nw_item.updated_at)
        self.assertNotEqual(nw_item.updated_at, 'Some other day')

    def test_requires_auth(self):
        resp = self.client.post('/social/posts/',
                                data={
                                    'content': 'Training hard',
                                    'is_private': False
                                })
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(NewsfeedItem.objects.count(), 0)
