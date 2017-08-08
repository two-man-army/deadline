from collections import OrderedDict

from django.test import TestCase

from accounts.serializers import UserSerializer
from challenges.tests.base import TestHelperMixin
from errors import DisabledSerializerError
from social.models import NewsfeedItem, NewsfeedItemComment
from social.serializers import NewsfeedItemCommentSerializer


class NewsfeedItemCommentTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.nw_item = NewsfeedItem.objects.create(author=self.auth_user, type='TEXT_POST',
                                              content={'content': 'Hello I like turtles'})
        self.comment_1 = NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=self.nw_item)
        self.comment_2 = NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=self.nw_item)
        self.comment_3 = NewsfeedItemComment.objects.create(author=self.auth_user, content='Drop the top', newsfeed_item=self.nw_item)

    def test_model_creation(self):
        self.assertEqual(self.nw_item.comments.count(), 3)
        self.assertIn(self.comment_1, self.nw_item.comments.all())
        self.assertIn(self.comment_2, self.nw_item.comments.all())
        self.assertIn(self.comment_3, self.nw_item.comments.all())

    def test_serialization(self):
        expected_data = {
            'id': self.comment_1.id,
            'content': self.comment_1.content,
            'author': OrderedDict(UserSerializer(instance=self.auth_user).data)
        }
        received_data = NewsfeedItemCommentSerializer(instance=self.comment_1).data
        self.assertEqual(expected_data, received_data)

    def test_deserialization_does_not_work(self):
        received_data = NewsfeedItemCommentSerializer(data={'author': self.auth_user.id, 'content': 'tank'})
        with self.assertRaises(DisabledSerializerError):
            received_data.save()
