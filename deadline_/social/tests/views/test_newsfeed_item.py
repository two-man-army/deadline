from datetime import timedelta, datetime
from unittest import TestCase
from unittest.mock import patch

from rest_framework.test import APITestCase

from accounts.models import User
from challenges.models import Submission
from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import UserFactory
from social.constants import NEWSFEED_ITEMS_PER_PAGE, NW_ITEM_TEXT_POST, NW_ITEM_SUBMISSION_LINK_POST, \
    NW_ITEM_CHALLENGE_LINK_POST, NW_ITEM_CHALLENGE_COMPLETION_POST
from social.models import NewsfeedItem
from social.serializers import NewsfeedItemSerializer
from social.views import NewsfeedItemDetailView, NewsfeedItemDetailManageView, SharePostCreateView, PostCreateView, \
    TextPostCreateView, SubmissionLinkPostCreateView, ChallengeLinkPostCreateView, ChallengeCompletionPostCreateView


class NewsfeedItemDetailManageViewTests(TestCase):
    def test_views_by_method_is_mapped_correctly(self):
        self.assertEqual(len(NewsfeedItemDetailManageView.VIEWS_BY_METHOD.keys()), 2)
        self.assertEqual(NewsfeedItemDetailManageView.VIEWS_BY_METHOD['GET'], NewsfeedItemDetailView.as_view)
        self.assertEqual(NewsfeedItemDetailManageView.VIEWS_BY_METHOD['POST'], SharePostCreateView.as_view)


class SharePostCreateViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.nw_item_us2_1 = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

    @patch('social.models.NewsfeedItemManager.create_share_post')
    def test_create_share_post(self, mock_create_share_post):
        response = self.client.post(f'/social/feed/items/{self.nw_item_us2_1.id}', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 201)
        mock_create_share_post.assert_called_once_with(author=self.auth_user, shared_item=self.nw_item_us2_1)

    def test_cannot_create_a_share_pointing_to_a_share(self):
        share_item = NewsfeedItem.objects.create_share_post(author=self.auth_user, shared_item=self.nw_item_us2_1)

        with patch('social.models.NewsfeedItemManager.create_share_post') as mock_create_share_post:
            response = self.client.post(f'/social/feed/items/{share_item.id}', HTTP_AUTHORIZATION=self.auth_token)
            self.assertEqual(response.status_code, 400)
            mock_create_share_post.assert_not_called()

    @patch('social.models.NewsfeedItemManager.create_share_post')
    def test_requires_authentication(self, mock_create_share_post):
        response = self.client.post(f'/social/feed/items/{self.nw_item_us2_1.id}')
        self.assertEqual(response.status_code, 401)
        mock_create_share_post.assert_not_called()

    @patch('social.models.NewsfeedItemManager.create_share_post')
    def test_invalid_newsfeed_item_id_returns_404(self, mock_create_share_post):
        response = self.client.post('/social/feed/items/111', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)
        mock_create_share_post.assert_not_called()


class SubmissionLinkPostCreateViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    @patch('social.models.NewsfeedItemManager.create_submission_link')
    def test_creation(self, mock_create_subm):
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'post_type': NW_ITEM_SUBMISSION_LINK_POST,
                                          'submission_id': self.submission.id})
        self.assertEqual(response.status_code, 201)
        mock_create_subm.assert_called_once_with(author=self.auth_user, submission=self.submission)

    @patch('social.models.NewsfeedItemManager.create_submission_link')
    def test_requires_auth(self, mock_create_subm):
        response = self.client.post('/social/posts',
                                    data={'post_type': NW_ITEM_SUBMISSION_LINK_POST,
                                          'submission_id': self.submission.id})
        self.assertEqual(response.status_code, 401)
        mock_create_subm.assert_not_called()

    @patch('social.models.NewsfeedItemManager.create_submission_link')
    def test_can_share_own_submission_even_if_not_fully_solved(self, mock_create_subm):
        subm = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                    author=self.auth_user, code="", result_score=self.challenge.score-1)
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'post_type': NW_ITEM_SUBMISSION_LINK_POST,
                                          'submission_id': subm.id})
        self.assertEqual(response.status_code, 201)
        mock_create_subm.assert_called_once_with(author=self.auth_user, submission=subm)

    @patch('social.models.NewsfeedItemManager.create_submission_link')
    def test_can_share_other_users_submission_if_challenge_solved(self, mock_create_subm):
        new_user = User.objects.create(username='Somebody', password='123', email='Somebody@abv.bg',
                                             score=123, role=self.base_role)
        subm = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                         author=new_user, code="", result_score=self.challenge.score-1)
        Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                  code="", result_score=self.challenge.score, pending=False)
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'post_type': NW_ITEM_SUBMISSION_LINK_POST,
                                          'submission_id': subm.id})

        self.assertEqual(response.status_code, 201)
        mock_create_subm.assert_called_once_with(author=self.auth_user, submission=subm)

    @patch('social.models.NewsfeedItemManager.create_submission_link')
    def test_cannot_share_other_user_submission_if_not_solved(self, mock_create_subm):
        new_user = User.objects.create(username='Somebody', password='123', email='Somebody@abv.bg',
                                             score=123, role=self.base_role)
        subm = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                         author=new_user, code="", result_score=self.challenge.score-1)

        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'post_type': NW_ITEM_SUBMISSION_LINK_POST,
                                          'submission_id': subm.id})

        self.assertEqual(response.status_code, 400)
        mock_create_subm.assert_not_called()

    @patch('social.models.NewsfeedItemManager.create_submission_link')
    def test_invalid_submission_id_returns_404(self, mock_create_subm):
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'post_type': NW_ITEM_SUBMISSION_LINK_POST,
                                          'submission_id': 111})
        self.assertEqual(response.status_code, 404)
        mock_create_subm.assert_not_called()


class ChallengeLinkPostCreateViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    @patch('social.models.NewsfeedItemManager.create_challenge_link')
    def test_creation(self, mock_create_challenge_link):
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'post_type': NW_ITEM_CHALLENGE_LINK_POST,
                                          'challenge_id': self.challenge.id})
        self.assertEqual(response.status_code, 201)
        mock_create_challenge_link.assert_called_once_with(author=self.auth_user, challenge=self.challenge)

    @patch('social.models.NewsfeedItemManager.create_challenge_link')
    def test_requires_auth(self, mock_create_challenge_link):
        response = self.client.post('/social/posts',
                                    data={'post_type': NW_ITEM_CHALLENGE_LINK_POST,
                                          'challenge_id': self.challenge.id})
        self.assertEqual(response.status_code, 401)
        mock_create_challenge_link.assert_not_called()

    @patch('social.models.NewsfeedItemManager.create_challenge_link')
    def test_invalid_challenge_id_returns_404(self, mock_create_challenge_link):
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'post_type': NW_ITEM_CHALLENGE_LINK_POST,
                                          'challenge_id': 111})
        self.assertEqual(response.status_code, 404)
        mock_create_challenge_link.assert_not_called()


# NEXT TODO: Assure each PostCreate calls appropriate view
@patch('social.models.NewsfeedItemManager.create_challenge_completion_post')
class ChallengeCompletionPostCreateViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up()

    @patch('challenges.models.Submission.has_solved_challenge')
    def test_creates_completion(self, mock_has_solved, mock_create_post):
        mock_has_solved.return_value = True
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token, data={
            'post_type': NW_ITEM_CHALLENGE_COMPLETION_POST,
            'submission_id': self.submission.id,
        })
        self.assertEqual(response.status_code, 201)
        mock_create_post.assert_called_once_with(submission=self.submission)

    @patch('helpers.get_date_difference')
    def test_does_not_create_if_submission_not_eligible_for_post(self, mock_get_date_diff, mock_create_post):
        """
        There is a limit on how many minutes can pass
            before a submission is eligible for this kind of post
        """
        from social.constants import MAX_CHALLENGE_COMPLETION_SUBMISSION_EXPIRY_MINUTES
        mock_get_date_diff.return_value = timedelta(minutes=MAX_CHALLENGE_COMPLETION_SUBMISSION_EXPIRY_MINUTES + 1)
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token, data={
            'post_type': NW_ITEM_CHALLENGE_COMPLETION_POST,
            'submission_id': self.submission.id,
        })

        self.assertEqual(response.status_code, 400)
        mock_create_post.assert_not_called()

    def test_returns_400_if_submission_is_not_made_by_user(self, mock_create_post):
        other_user = UserFactory()
        other_user.save()
        other_subm = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                               author=other_user, code="")
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token, data={
            'post_type': NW_ITEM_CHALLENGE_COMPLETION_POST,
            'submission_id': other_subm.id,
        })

        self.assertEqual(response.status_code, 400)
        mock_create_post.assert_not_called()
        mock_create_post.assert_not_called()

    @patch('challenges.models.Submission.has_solved_challenge')
    def test_returns_400_if_submission_not_solved(self, mock_has_solved, mock_create_post):
        mock_has_solved.return_value = False
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token, data={
            'post_type': NW_ITEM_CHALLENGE_COMPLETION_POST,
            'submission_id': self.submission.id,
        })

        self.assertEqual(response.status_code, 400)
        mock_create_post.assert_not_called()

    def test_returns_404_if_invalid_submission(self, mock_create_post):
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token, data={
            'post_type': NW_ITEM_CHALLENGE_COMPLETION_POST,
            'submission_id': 111,
        })

        self.assertEqual(response.status_code, 404)
        mock_create_post.assert_not_called()

    def test_requires_auth(self, mock_create_post):
        response = self.client.post('/social/posts', data={
            'post_type': NW_ITEM_CHALLENGE_COMPLETION_POST,
            'submission_id': 111,
        })
        self.assertEqual(response.status_code, 401)
        mock_create_post.assert_not_called()


class PostCreateViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_has_correct_mapping(self):
        self.assertEqual(len(PostCreateView.VIEWS_BY_TYPE.keys()), 4)
        self.assertEqual(PostCreateView.VIEWS_BY_TYPE[NW_ITEM_TEXT_POST], TextPostCreateView.as_view)
        self.assertEqual(PostCreateView.VIEWS_BY_TYPE[NW_ITEM_SUBMISSION_LINK_POST], SubmissionLinkPostCreateView.as_view)
        self.assertEqual(PostCreateView.VIEWS_BY_TYPE[NW_ITEM_CHALLENGE_LINK_POST], ChallengeLinkPostCreateView.as_view)
        self.assertEqual(PostCreateView.VIEWS_BY_TYPE[NW_ITEM_CHALLENGE_COMPLETION_POST], ChallengeCompletionPostCreateView.as_view)

    def test_returns_400_onunsupported_type(self):
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token, data={'post_type': 'TANK'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Post Type is not supported!')

    def test_returns_400_on_empty_type(self):
        response = self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Post Type is not supported!')


class TextPostCreateViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_create_post(self):
        self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                         data={
                             'post_type': NW_ITEM_TEXT_POST,
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
        self.client.post('/social/posts', HTTP_AUTHORIZATION=self.auth_token,
                         data={
                             'post_type': NW_ITEM_TEXT_POST,
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
        resp = self.client.post('/social/posts',
                                data={
                                    'post_type': NW_ITEM_TEXT_POST,
                                    'content': 'Training hard',
                                    'is_private': False
                                })
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(NewsfeedItem.objects.count(), 0)


class NewsfeedContentViewTests(APITestCase, TestHelperMixin):
    """
    The newsfeed of a User should show NewsfeedItems
        by people he has followed + his
    """
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.nw_item_us2_1 = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
        self.nw_item_us2_2 = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

        self.user3 = User.objects.create(username='user3', password='123', email='user3@abv.bg', score=123, role=self.base_role)
        self.nw_item_us3_1 = NewsfeedItem.objects.create(author=self.user3, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

        self.user4 = User.objects.create(username='user4', password='123', email='user4@abv.bg', score=123, role=self.base_role)
        self.nw_item_us4_1 = NewsfeedItem.objects.create(author=self.user4, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

    def test_should_see_all_items_including_his(self):
        self.auth_user.follow(self.user2)
        newest_item = NewsfeedItem.objects.create(author=self.auth_user, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'},
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

        first_two_items = [NewsfeedItem.objects.create(author=self.user5, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'}), NewsfeedItem.objects.create(author=self.user5, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})]
        for i in range(NEWSFEED_ITEMS_PER_PAGE):
            NewsfeedItem.objects.create(author=self.user5, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
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
            NewsfeedItem.objects.create(author=self.user5, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

        response = self.client.get('/social/feed', HTTP_AUTHORIZATION=self.auth_token)
        expected_data = self.client.get('/social/feed?page=1', HTTP_AUTHORIZATION=self.auth_token).data

        self.assertEqual(len(response.data['items']), NEWSFEED_ITEMS_PER_PAGE)
        self.assertEqual(response.data, expected_data)


class NewsfeedItemDetailViewTests(APITestCase, TestHelperMixin):
    """
    Should simply return information about a specific NewsfeedItem
    """
    def setUp(self):
        self.create_user_and_auth_token()
        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.nw_item_us2_1 = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

    def test_returns_serialized_nw_item(self):
        response = self.client.get(self.nw_item_us2_1.get_absolute_url(), HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, NewsfeedItemSerializer(self.nw_item_us2_1).data)

    def test_requires_authentication(self):
        response = self.client.get(self.nw_item_us2_1.get_absolute_url())
        self.assertEqual(response.status_code, 401)

    def test_no_item_returns_404(self):
        response = self.client.get('/social/feed/items/111', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)

