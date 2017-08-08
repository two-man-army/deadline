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

    # TODO: MORE