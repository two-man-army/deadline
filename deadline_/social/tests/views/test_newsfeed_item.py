from datetime import timedelta, datetime

from rest_framework.test import APITestCase

from accounts.models import User
from challenges.tests.base import TestHelperMixin
from social.constants import NEWSFEED_ITEMS_PER_PAGE
from social.models import NewsfeedItem
from social.serializers import NewsfeedItemSerializer


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
                             'like_count': 200,
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


class NewsfeedGetViewTests(APITestCase, TestHelperMixin):
    """
    The newsfeed of a User should show NewsfeedItems
        by people he has followed + his
    """
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.nw_item_us2_1 = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})
        self.nw_item_us2_2 = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})

        self.user3 = User.objects.create(username='user3', password='123', email='user3@abv.bg', score=123, role=self.base_role)
        self.nw_item_us3_1 = NewsfeedItem.objects.create(author=self.user3, type='TEXT_POST', content={'content': 'Hi'})

        self.user4 = User.objects.create(username='user4', password='123', email='user4@abv.bg', score=123, role=self.base_role)
        self.nw_item_us4_1 = NewsfeedItem.objects.create(author=self.user4, type='TEXT_POST', content={'content': 'Hi'})

    def test_should_see_all_items_including_his(self):
        self.auth_user.follow(self.user2)
        newest_item = NewsfeedItem.objects.create(author=self.auth_user, type='TEXT_POST', content={'content': 'Hi'},
                                                  created_at=datetime.now() + timedelta(days=1))

        expected_items = NewsfeedItemSerializer(many=True)\
            .to_representation([newest_item, self.nw_item_us2_2, self.nw_item_us2_1], user=self.auth_user)

        response = self.client.get('/social/feed', HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_items, response.data['items'])

    def test_empty_feed_returns_empty(self):
        response = self.client.get('/social/feed', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([], response.data['items'])

    def test_requires_auth(self):
        response = self.client.get('/social/feed')
        self.assertEqual(response.status_code, 401)

    def test_pagination_works(self):
        self.user5 = User.objects.create(username='user5', password='123', email='user5@abv.bg', score=123, role=self.base_role)
        self.auth_user.follow(self.user5)
        # Create 2 more than what will be shown in the first page and query for the second page

        first_two_items = [NewsfeedItem.objects.create(author=self.user5, type='TEXT_POST', content={'content': 'Hi'}), NewsfeedItem.objects.create(author=self.user5, type='TEXT_POST', content={'content': 'Hi'})]
        for i in range(NEWSFEED_ITEMS_PER_PAGE):
            NewsfeedItem.objects.create(author=self.user5, type='TEXT_POST', content={'content': 'Hi'})
        expected_items = NewsfeedItemSerializer(many=True)\
            .to_representation(reversed(first_two_items), user=self.auth_user)

        response = self.client.get('/social/feed?page=2', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['items'], expected_items)

    def test_pagination_with_invalid_page(self):
        """ Should just give him the first page """
        self.auth_user.follow(self.user2)

        response = self.client.get('/social/feed?page=TANK', HTTP_AUTHORIZATION=self.auth_token)
        normal_data = self.client.get('/social/feed?page=1', HTTP_AUTHORIZATION=self.auth_token).data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, normal_data)

    def test_returns_first_page_if_no_querystring(self):
        # Create twice as much posts and assert only the first half is shown
        self.user5 = User.objects.create(username='user5', password='123', email='user5@abv.bg', score=123, role=self.base_role)
        self.auth_user.follow(self.user5)
        for i in range(NEWSFEED_ITEMS_PER_PAGE * 2):
            NewsfeedItem.objects.create(author=self.user5, type='TEXT_POST', content={'content': 'Hi'})

        response = self.client.get('/social/feed', HTTP_AUTHORIZATION=self.auth_token)
        expected_data = self.client.get('/social/feed?page=1', HTTP_AUTHORIZATION=self.auth_token).data

        self.assertEqual(len(response.data['items']), NEWSFEED_ITEMS_PER_PAGE)
        self.assertEqual(response.data, expected_data)
