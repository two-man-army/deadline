from rest_framework.test import APITestCase

from accounts.models import User
from challenges.tests.base import TestHelperMixin
from social.models import NewsfeedItem
from social.views import NewsfeedItemLikeManageView, NewsfeedItemLikeCreateView


class NewsfeedItemLikeManageViewTests(APITestCase, TestHelperMixin):
    def test_points_to_right_views(self):
        views_by_methods = NewsfeedItemLikeManageView.VIEWS_BY_METHOD
        self.assertEqual(views_by_methods['POST'], NewsfeedItemLikeCreateView.as_view)
        self.assertEqual(len(views_by_methods.keys()), 1)


class NewsfeedItemLikeCreateViewTests(APITestCase, TestHelperMixin):
    """
    Should simply set a Like on the NewsfeedItem
    """
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.user2_token = 'Token {}'.format(self.user2.auth_token.key)
        self.nw_item_us2_1 = NewsfeedItem.objects.create(author=self.user2, type='TEXT_POST', content={'content': 'Hi'})

    def test_like(self):
        response = self.client.post(f'/social/feed/items/{self.nw_item_us2_1.id}/likes', HTTP_AUTHORIZATION=self.user2_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.nw_item_us2_1.likes.count(), 1)
        self.assertEqual(self.nw_item_us2_1.likes.first().author, self.user2)

    def test_already_liked_returns_400(self):
        self.nw_item_us2_1.like(self.user2)
        response = self.client.post(f'/social/feed/items/{self.nw_item_us2_1.id}/likes', HTTP_AUTHORIZATION=self.user2_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.nw_item_us2_1.likes.count(), 1)

    def test_invalid_nw_item_id_returns_404(self):
        response = self.client.post(f'/social/feed/items/111/likes', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

    def test_requires_authentication(self):
        response = self.client.post(f'/social/feed/items/111/likes')
        self.assertEqual(response.status_code, 401)
