from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from social.models import NewsfeedItem, NewsfeedItemComment


class NewsfeedItemCommentTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_model_creation(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type='TEXT_POST',
                                              content={'content': 'Hello I like turtles'})
        comment_1 = NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        comment_2 = NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        comment_3 = NewsfeedItemComment.objects.create(author=self.auth_user, content='Drop the top', newsfeed_item=nw_item)

        self.assertEqual(nw_item.comments.count(), 3)
        self.assertIn(comment_1, nw_item.comments.all())
        self.assertIn(comment_2, nw_item.comments.all())
        self.assertIn(comment_3, nw_item.comments.all())
