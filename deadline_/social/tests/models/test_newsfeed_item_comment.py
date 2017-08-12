from collections import OrderedDict

from django.test import TestCase

from accounts.serializers import UserSerializer
from challenges.tests.base import TestHelperMixin
from social.constants import NW_ITEM_TEXT_POST
from social.models import NewsfeedItem, NewsfeedItemComment
from social.serializers import NewsfeedItemCommentSerializer


class NewsfeedItemCommentTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                                   content={'content': 'Hello I like turtles'})
        self.comment_1 = NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=self.nw_item)
        self.comment_2 = NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=self.nw_item)
        self.comment_3 = NewsfeedItemComment.objects.create(author=self.auth_user, content='Drop the top', newsfeed_item=self.nw_item)

    def test_model_creation(self):
        self.assertEqual(self.nw_item.comments.count(), 3)
        self.assertIn(self.comment_1, self.nw_item.comments.all())
        self.assertIn(self.comment_2, self.nw_item.comments.all())
        self.assertIn(self.comment_3, self.nw_item.comments.all())

    def test_can_add_reply(self):
        reply = self.comment_1.add_reply(self.auth_user, 'whats UP :)')

        self.assertEqual(self.comment_1.replies.count(), 1)
        self.assertEqual(self.comment_1.replies.first(), reply)
        self.assertEqual(reply.author, self.auth_user)
        self.assertEqual(reply.newsfeed_item, self.comment_1.newsfeed_item)
        self.assertEqual(reply.content, 'whats UP :)')

    def test_deserialization(self):
        ser = NewsfeedItemCommentSerializer(data={'content': 'Tankkk'})
        self.assertTrue(ser.is_valid())
        nw_comment = ser.save(author_id=self.auth_user.id, newsfeed_item_id=self.nw_item.id)
        self.assertEqual(nw_comment.author, self.auth_user)
        self.assertEqual(nw_comment.content, 'Tankkk')
        self.assertEqual(nw_comment.newsfeed_item, self.nw_item)

    def test_deserialization_uneditable_fields(self):
        """ author and newsfeed_item should not be editable"""
        ser = NewsfeedItemCommentSerializer(data={'content': 'Tankkk', 'author_id': self.auth_user.id,
                                                  'author': self.auth_user.id, 'newsfeed_item_id': self.nw_item.id,
                                                  'newsfeed_item': self.nw_item.id})
        self.assertTrue(ser.is_valid())
        with self.assertRaises(Exception):
            ser.save()

    def test_serialization(self):
        expected_data = {
            'id': self.comment_1.id,
            'content': self.comment_1.content,
            'author': OrderedDict(UserSerializer(instance=self.auth_user).data),
            'replies': []
        }
        received_data = NewsfeedItemCommentSerializer(instance=self.comment_1).data
        self.assertEqual(expected_data, received_data)

    def test_nested_serialization(self):
        author_data = OrderedDict(UserSerializer(instance=self.auth_user).data)
        reply_1 = self.comment_1.add_reply(author=self.auth_user, content='sup')
        reply_2 = self.comment_1.add_reply(author=self.auth_user, content='sup')
        reply_1_reply = reply_1.add_reply(author=self.auth_user, content='sup')
        reply_1_reply_reply = reply_1_reply.add_reply(author=self.auth_user, content='sup')

        # Also confirms that replies are sorted by created date descending
        expected_data = {
            'id': self.comment_1.id,
            'content': self.comment_1.content,
            'author': author_data,
            'replies': [
                {
                    'id': reply_2.id,
                    'content': reply_2.content,
                    'author': author_data,
                    'replies': [],
                },
                {

                    'id': reply_1.id,
                    'content': reply_1.content,
                    'author': author_data,
                    'replies': [
                        {
                            'id': reply_1_reply.id,
                            'content': reply_1_reply.content,
                            'author': author_data,
                            'replies': [
                                {
                                    'id': reply_1_reply_reply.id,
                                    'content': reply_1_reply_reply.content,
                                    'author': author_data,
                                    'replies': [],
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        received_data = NewsfeedItemCommentSerializer(instance=self.comment_1).data
        self.assertEqual(expected_data, received_data)
