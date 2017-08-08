from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from social.models import NewsfeedItem


class NewsfeedItemTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_model_creation(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type='TEXT_POST',
                                              content={'content': 'Hello I like turtles'})
        self.assertEqual(nw_item.author, self.auth_user)
        self.assertEqual(nw_item.type, 'TEXT_POST')
        self.assertEqual(nw_item.content, {'content': 'Hello I like turtles'})
        self.assertEqual(nw_item.is_private, False)
        self.assertIsNotNone(nw_item.created_at)
        self.assertIsNotNone(nw_item.updated_at)
