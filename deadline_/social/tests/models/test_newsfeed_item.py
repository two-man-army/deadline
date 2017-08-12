from django.test import TestCase

from accounts.serializers import UserSerializer
from challenges.models import MainCategory, SubCategory, Proficiency, UserSubcategoryProficiency
from challenges.tests.base import TestHelperMixin
from social.constants import NW_ITEM_TEXT_POST, NW_ITEM_SHARE_POST
from social.models import NewsfeedItem, NewsfeedItemComment, NewsfeedItemLike
from social.errors import InvalidNewsfeedItemContentField, InvalidNewsfeedItemType, MissingNewsfeedItemContentField, \
    LikeAlreadyExistsError, NonExistentLikeError
from social.serializers import NewsfeedItemSerializer, NewsfeedItemCommentSerializer


class NewsfeedItemTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_text_post_creation(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        self.assertEqual(nw_item.author, self.auth_user)
        self.assertEqual(nw_item.type, NW_ITEM_TEXT_POST)
        self.assertEqual(nw_item.content, {'content': 'Hello I like turtles'})
        self.assertEqual(nw_item.is_private, False)
        self.assertIsNotNone(nw_item.created_at)
        self.assertIsNotNone(nw_item.updated_at)

    def test_share_post_creation(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        nw_share_item = NewsfeedItem.objects.create_share_post(shared_item=nw_item, author=self.auth_user)

        self.assertEqual(nw_share_item.type, NW_ITEM_SHARE_POST)
        self.assertEqual(nw_share_item.author, self.auth_user)
        self.assertEqual(len(nw_share_item.content.keys()), 1)
        self.assertEqual(nw_share_item.content['newsfeed_item_id'], nw_item.id)

    def test_subcategory_badge_post_creation(self):
        challenge_cat = MainCategory.objects.create(name='Tests')
        sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        prof = Proficiency.objects.create(name='Tank', needed_percentage=5)
        user_subcat_progress = UserSubcategoryProficiency.objects.create(user=self.auth_user, subcategory=sub_cat,
                                                                         proficiency=prof, user_score=0)

        nw_item = NewsfeedItem.objects.create_subcategory_badge_post(user_subcat_progress)
        self.assertEqual(len(nw_item.content.keys()), 3)
        self.assertEqual(nw_item.content['subcategory_id'], sub_cat.id)
        self.assertEqual(nw_item.content['subcategory_name'], sub_cat.name)
        self.assertEqual(nw_item.content['proficiency_name'], prof.name)

    def test_get_absolute_url(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        self.assertEqual(nw_item.get_absolute_url(), f'/social/feed/items/{nw_item.id}')

    def test_serialiation(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        NewsfeedItemComment.objects.create(author=self.auth_user, content='Drop the top', newsfeed_item=nw_item)
        NewsfeedItemLike.objects.create(author=self.auth_user, newsfeed_item=nw_item)
        serializer = NewsfeedItemSerializer(instance=nw_item)

        expected_data = {
            'id': nw_item.id,
            'author': UserSerializer().to_representation(instance=self.auth_user),
            'type': nw_item.type,
            'comments': NewsfeedItemCommentSerializer(many=True).to_representation(nw_item.comments.all()),
            'content': nw_item.content,
            'is_private': nw_item.is_private,
            'created_at': nw_item.created_at.isoformat().replace('+00:00', 'Z'),
            'updated_at': nw_item.updated_at.isoformat().replace('+00:00', 'Z'),
            'like_count': 1
        }
        received_data = serializer.data

        self.assertEqual(received_data, expected_data)

    def test_serializer_with_user_variable(self):
        # If we pass a User to the to_representation call, a 'user_has_liked' field should appear
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        NewsfeedItemComment.objects.create(author=self.auth_user, content='Drop the top', newsfeed_item=nw_item)
        nw_like = NewsfeedItemLike.objects.create(author=self.auth_user, newsfeed_item=nw_item)
        serializer = NewsfeedItemSerializer()

        expected_data = {
            'id': nw_item.id,
            'author': UserSerializer().to_representation(instance=self.auth_user),
            'type': nw_item.type,
            'comments': NewsfeedItemCommentSerializer(many=True).to_representation(nw_item.comments.all()),
            'content': nw_item.content,
            'is_private': nw_item.is_private,
            'created_at': nw_item.created_at.isoformat().replace('+00:00', 'Z'),
            'updated_at': nw_item.updated_at.isoformat().replace('+00:00', 'Z'),
            'like_count': 1,
            'user_has_liked': True
        }
        received_data = serializer.to_representation(instance=nw_item, user=self.auth_user)
        self.assertEqual(received_data, expected_data)

        nw_like.delete()
        nw_item.refresh_from_db()
        received_data = serializer.to_representation(instance=nw_item, user=self.auth_user)
        # test to see if the user_has_liked will be changed as appropriate
        self.assertFalse(received_data['user_has_liked'])

    def test_list_serialization(self):
        """
        This tests our custom ListSerializer class and assures it attaches the user_has_liked variable
        """
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        NewsfeedItemComment.objects.create(author=self.auth_user, content='name', newsfeed_item=nw_item)
        NewsfeedItemComment.objects.create(author=self.auth_user, content='Drop the top', newsfeed_item=nw_item)
        NewsfeedItemLike.objects.create(author=self.auth_user, newsfeed_item=nw_item)
        serializer = NewsfeedItemSerializer(many=True)

        nw_item_repr = {
            'id': nw_item.id,
            'author': UserSerializer().to_representation(instance=self.auth_user),
            'type': nw_item.type,
            'comments': NewsfeedItemCommentSerializer(many=True).to_representation(nw_item.comments.all()),
            'content': nw_item.content,
            'is_private': nw_item.is_private,
            'created_at': nw_item.created_at.isoformat().replace('+00:00', 'Z'),
            'updated_at': nw_item.updated_at.isoformat().replace('+00:00', 'Z'),
            'like_count': 1,
            'user_has_liked': True
        }

        expected_data = [nw_item_repr, nw_item_repr]
        received_data = serializer.to_representation(data=[nw_item, nw_item], user=self.auth_user)

        self.assertEqual(expected_data, received_data)

    def test_model_save_raises_if_invalid_newsfeed_type(self):
        """ An error should be raised if we enter an invalid newsfeeditem type """
        with self.assertRaises(InvalidNewsfeedItemType):
            NewsfeedItem.objects.create(author=self.auth_user, type='TANK',
                                        content={'content': 'Hello I like turtles'})

    def test_model_save_raises_if_missing_newsfeed_content_field(self):
        """ Given a valid Newsfeed Type, an error should be raised if a required field is missing """
        with self.assertRaises(MissingNewsfeedItemContentField):
            NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                        content={})

    def test_model_save_raises_if_invalid_newsfeed_content_field(self):
        """ Given a valid Newsfeed Type, an error should be raised if an invalid field is added,
                regardless if all the right ones are supplied (memory is expensive) """
        with self.assertRaises(InvalidNewsfeedItemContentField):
            NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                        content={'content': 'Hello I like turtles', 'tank': 'yo'})

    def test_like_should_add_to_likes(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        nw_item.like(self.auth_user)

        self.assertEqual(nw_item.likes.count(), 1)
        self.assertEqual(nw_item.likes.first().author, self.auth_user)

    def test_duplicate_like_raises_error(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        nw_item.like(self.auth_user)

        with self.assertRaises(LikeAlreadyExistsError):
            nw_item.like(self.auth_user)

        self.assertEqual(nw_item.likes.count(), 1)
        self.assertEqual(nw_item.likes.first().author, self.auth_user)

    def test_remove_like_removes_like(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        nw_item.like(self.auth_user)
        self.assertEqual(nw_item.likes.count(), 1)

        nw_item.remove_like(self.auth_user)
        self.assertEqual(nw_item.likes.count(), 0)

    def test_remove_non_existent_like_raises(self):
        nw_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST,
                                              content={'content': 'Hello I like turtles'})
        with self.assertRaises(NonExistentLikeError):
            nw_item.remove_like(self.auth_user)
