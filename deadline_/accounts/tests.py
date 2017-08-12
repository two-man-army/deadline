from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock

from django.http import HttpResponse
from django.test import TestCase
from django.utils.six import BytesIO
from rest_framework.test import APITestCase
from rest_framework.parsers import JSONParser

from accounts.errors import UserAlreadyFollowedError, UserNotFollowedError
from accounts.models import User, Role
from accounts.serializers import UserSerializer
from challenges.tests.factories import UserFactory, ChallengeDescFactory
from social.constants import NW_ITEM_TEXT_POST
from social.models import NewsfeedItem


class UserModelNewsfeedTest(TestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.main_user = User.objects.create(username='main_user', password='123', email='main_user@abv.bg', score=123, role=self.base_role)

        self.user2 = User.objects.create(username='user2', password='123', email='user2@abv.bg', score=123, role=self.base_role)
        self.nw_item_us2_1 = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
        self.nw_item_us2_2 = NewsfeedItem.objects.create(author=self.user2, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

        self.user3 = User.objects.create(username='user3', password='123', email='user3@abv.bg', score=123, role=self.base_role)
        self.nw_item_us3_1 = NewsfeedItem.objects.create(author=self.user3, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

        self.user4 = User.objects.create(username='user4', password='123', email='user4@abv.bg', score=123, role=self.base_role)
        self.nw_item_us4_1 = NewsfeedItem.objects.create(author=self.user4, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

    def test_fetch_newsfeed(self):
        # Should return all the people the user has followed's items, sorted by date
        self.main_user.follow(self.user2)
        self.main_user.follow(self.user4)

        expected_items = NewsfeedItem.objects \
            .filter(author_id__in=[us.id for us in self.main_user.users_followed.all()] + [self.main_user.id]) \
            .order_by('-created_at')

        received_items = self.main_user.fetch_newsfeed()

        self.assertEqual(len(received_items), 3)
        self.assertEqual(len(received_items), len(expected_items))
        for i in range(3):
            self.assertEqual(expected_items[i], received_items[i])

    def test_fetch_newsfeed_receives_own_items_as_well(self):
        nw_item1 = NewsfeedItem.objects.create(author=self.main_user, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
        nw_item2 = NewsfeedItem.objects.create(author=self.main_user, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})

        received_items = self.main_user.fetch_newsfeed()

        self.assertEqual(len(received_items), 2)
        self.assertEqual([nw_item2, nw_item1], list(received_items))

    def test_fetch_newsfeed_receives_items_ordered_by_date(self):
        self.user5 = User.objects.create(username='user5', password='123', email='user5@abv.bg', score=123, role=self.base_role)
        self.main_user.follow(self.user5)
        self.latest_item = NewsfeedItem.objects.create(author=self.user5, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
        self.latest_item.created_at = datetime.now() + timedelta(days=1)
        self.oldest_item = NewsfeedItem.objects.create(author=self.user5, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
        self.oldest_item.created_at = datetime.now() - timedelta(days=1)
        self.mid_item = NewsfeedItem.objects.create(author=self.user5, type=NW_ITEM_TEXT_POST, content={'content': 'Hi'})
        self.oldest_item.save(); self.latest_item.save()

        received_items = self.main_user.fetch_newsfeed()
        self.assertEqual(list(received_items), [self.latest_item, self.mid_item, self.oldest_item])

    def test_fetch_newsfeed_supports_pagination(self):
        self.main_user.follow(self.user2)
        self.main_user.follow(self.user3)
        self.main_user.follow(self.user4)

        expected_items = NewsfeedItem.objects \
            .filter(author_id__in=[us.id for us in self.main_user.users_followed.all()] + [self.main_user.id]) \
            .order_by('-created_at')[2:3]

        received_items = self.main_user.fetch_newsfeed(2, 3)

        self.assertEqual(len(received_items), len(expected_items))
        for i in range(len(expected_items)):
            self.assertEqual(expected_items[i], received_items[i])


class UserModelTest(TestCase):
    def setUp(self):
        from challenges.models import MainCategory, SubCategory, Proficiency
        self.base_role = Role.objects.create(name='User')
        self.main_cat = MainCategory.objects.create(name='tank')
        self.main_cat2 = MainCategory.objects.create(name='helicopter')
        self.sub1 = SubCategory.objects.create(name='AAX-190', meta_category=self.main_cat, max_score=250)
        self.sub2 = SubCategory.objects.create(name='MX-5', meta_category=self.main_cat2, max_score=250)
        self.advanced_proficiency = Proficiency.objects.create(name="test", needed_percentage=21)
        self.starter_proficiency = Proficiency.objects.create(name="scrub", needed_percentage=0)

    def test_user_register_creates_token(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        self.assertTrue(hasattr(us, 'auth_token'))
        self.assertIsNotNone(us.auth_token)

    def test_user_register_assigns_default_user_role(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        self.assertEqual(us.role, self.base_role)

    def test_user_register_creates_user_subcategory_proficiency(self):
        from challenges.models import UserSubcategoryProficiency
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.save()

        received: UserSubcategoryProficiency = UserSubcategoryProficiency.objects.filter(user=us, subcategory=self.sub1).first()
        self.assertEqual(received.proficiency, self.starter_proficiency)
        received_sub2: UserSubcategoryProficiency = UserSubcategoryProficiency.objects.filter(user=us, subcategory=self.sub2).first()
        self.assertEqual(received_sub2.proficiency, self.starter_proficiency)

    def test_user_register_requires_unique_username(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.save()
        with self.assertRaises(Exception):
            us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
            us.save()

    def test_serialization(self):
        """ Should convert a user object to a json """
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role_id=self.base_role.id)
        expected_data = {'id': us.id, 'username': us.username, 'email': us.email,
                         'score': us.score, 'role': {'id': us.role.id, 'name': us.role.name}}
        self.assertEqual(UserSerializer(us).data, expected_data)

    def test_deserialization(self):
        expected_json = bytes(
            ('{"id":1,"username":"SomeGuy","email":"me@abv.bg",'
            f'"password":"123","score":123, "role": {self.base_role.id}}}'), encoding='utf-8')

        data = JSONParser().parse(BytesIO(expected_json))
        serializer = UserSerializer(data=data)
        serializer.is_valid()
        deser_user = serializer.save()

        self.assertIsInstance(deser_user, User)
        self.assertEqual(deser_user.username, 'SomeGuy')
        self.assertEqual(deser_user.email, 'me@abv.bg')
        self.assertNotEqual(deser_user.password, '123')  # should be hashed!
        self.assertEqual(deser_user.score, 123)

    def test_user_can_follow_another_user(self):
        user_who_gets_followed = User.objects.create(username='SomeFollowee', email='me@abv.bg', password='123', score=123, role=self.base_role)
        follower = User.objects.create(username='SomeGuy', email='follower@abv.bg', password='123', score=123, role=self.base_role)

        follower.follow(user_who_gets_followed)

        self.assertEqual(follower.users_followed.count(), 1)
        self.assertEqual(follower.followers.count(), 0)
        self.assertIn(user_who_gets_followed, follower.users_followed.all())

        self.assertEqual(user_who_gets_followed.followers.count(), 1)
        self.assertEqual(user_who_gets_followed.users_followed.count(), 0)

    def test_cannot_have_duplicate_follower(self):
        user_who_gets_followed = User.objects.create(username='SomeFollowee', email='me@abv.bg', password='123', score=123, role=self.base_role)
        follower = User.objects.create(username='SomeGuy', email='follower@abv.bg', password='123', score=123, role=self.base_role)
        follower.follow(user_who_gets_followed)
        with self.assertRaises(UserAlreadyFollowedError):
            follower.follow(user_who_gets_followed)

    def test_user_can_unfollow_another_user(self):
        user_who_gets_followed = User.objects.create(username='SomeFollowee', email='me@abv.bg', password='123', score=123, role=self.base_role)
        follower = User.objects.create(username='SomeGuy', email='follower@abv.bg', password='123', score=123, role=self.base_role)
        follower.follow(user_who_gets_followed)
        self.assertEqual(follower.users_followed.count(), 1)

        follower.unfollow(user_who_gets_followed)
        self.assertEqual(follower.users_followed.count(), 0)

    def test_unfollow_user_that_is_not_followed_raises_error(self):
        user_who_gets_followed = User.objects.create(username='SomeFollowee', email='me@abv.bg', password='123', score=123, role=self.base_role)
        follower = User.objects.create(username='SomeGuy', email='follower@abv.bg', password='123', score=123, role=self.base_role)
        with self.assertRaises(UserNotFollowedError):
            follower.unfollow(user_who_gets_followed)

    def test_get_vote_for_submission_returns_vote(self):
        from challenges.models import Challenge, Submission, SubCategory, MainCategory, ChallengeDescription, Language, \
            SubmissionVote
        python_language = Language(name="Python") ;python_language.save()
        challenge_cat = MainCategory.objects.create(name='Tests'); challenge_cat.save()
        sub_cat = SubCategory(name='tests', meta_category=challenge_cat); sub_cat.save()
        challenge = Challenge(name='Hello', difficulty=5, score=10, description=ChallengeDescFactory(),
                                   test_case_count=3,
                                   category=sub_cat); challenge.save()
        auth_user = UserFactory()
        auth_user.save()
        s = Submission(language=python_language, challenge=challenge, author=auth_user,
                       code='a')
        s.save()
        sv1 = SubmissionVote(author=auth_user, submission=s, is_upvote=False)
        sv1.save()

        received_vote = auth_user.get_vote_for_submission(submission_id=s.id)
        self.assertEqual(received_vote, sv1)

    def test_get_vote_for_submission_no_vote_returns_None(self):
        auth_user = UserFactory()
        self.assertIsNone(auth_user.get_vote_for_submission(submission_id=1))

    @patch('challenges.models.Submission.fetch_top_submission_for_challenge_and_user')
    def test_fetch_max_score_for_challenge(self, fetch_mock):
        """ Should call the submission's fetch_top_submission method"""
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.save()
        fetch_mock.return_value = MagicMock(maxscore=5)

        received_score = us.fetch_max_score_for_challenge(1)

        fetch_mock.assert_called_once_with(1, us.id)
        self.assertEqual(received_score, 5)


    @patch('challenges.models.Submission.fetch_top_submission_for_challenge_and_user')
    def test_fetch_max_score_for_challenge_return_0_on_none_value(self, fetch_mock):
        """ Should return 0 if no such score exists"""
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.save()
        fetch_mock.return_value = None

        received_score = us.fetch_max_score_for_challenge(1)

        fetch_mock.assert_called_once_with(1, us.id)
        self.assertEqual(received_score, 0)

    def test_fetch_subcategory_proficiency(self):
        """
        Should return a UserSubcategoryProficiency model
        """
        from challenges.models import UserSubcategoryProficiency, SubCategory, MainCategory
        # from challenges.tests.factories import SubCategoryFactory, MainCategoryFactory
        mc = MainCategory.objects.create(name='t')
        mc.save()
        sc = SubCategory(name='tank', meta_category=mc)
        sc.save()
        user = UserFactory()
        user.save()  # should create the UserSubcatProficiency objects
        expected_model = UserSubcategoryProficiency.objects.filter(subcategory=sc).first()

        usp: UserSubcategoryProficiency = user.fetch_subcategory_proficiency(subcategory_id=sc.id)

        self.assertEqual(expected_model, usp)

    def test_fetch_invalid_subcategory_proficiency(self):
        """
        Should raise an exception
        """
        user = UserFactory()
        user.save()  # should create the UserSubcatProficiency objects
        with self.assertRaises(Exception):
            usp: UserSubcategoryProficiency = user.fetch_subcategory_proficiency(subcategory_id=255)

    def test_fetch_subcategory_proficiency(self):
        """
        Should return a Proficiency object
        """
        from challenges.models import UserSubcategoryProficiency, Proficiency, MainCategory, SubCategory
        mc = MainCategory.objects.create(name='t')
        mc.save()
        sc = SubCategory.objects.create(name='tank', meta_category=mc)
        sc.save()
        user: User = UserFactory()
        user.save()  # should create the UserSubcatProgress objects

        received_prof = user.fetch_proficiency_by_subcategory(sc.id)

        self.assertEqual(received_prof, self.starter_proficiency)

    def test_fetch_invalid_subcategory_proficiency(self):
        """ Should raise """
        user = UserFactory()
        user.save()  # should create the UserSubcatProgress objects
        with self.assertRaises(Exception):
            usp = user.fetch_subcategory_proficiency(subcategory_id=255)

    def test_fetch_overall_leaderboard_position(self):
        """ Should return the user's leaderboard position """
        first_user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        second_user = User.objects.create(username='dGuy', email='d@abv.dg', password='123', score=122, role=self.base_role)
        second_user2 = User.objects.create(username='dGumasky', email='molly@abv.bg', password='123', score=122, role=self.base_role)
        second_user3 = User.objects.create(username='xdGumasky', email='xmolly@abv.bg', password='123', score=122, role=self.base_role)
        fifth_user = User.objects.create(username='dbrr', email='dd@abv.bg', password='123', score=121, role=self.base_role)
        fifth_user.save()

        self.assertEqual(fifth_user.fetch_overall_leaderboard_position(), 5)
        self.assertEqual(second_user.fetch_overall_leaderboard_position(), 2)
        self.assertEqual(second_user2.fetch_overall_leaderboard_position(), 2)
        self.assertEqual(second_user3.fetch_overall_leaderboard_position(), 2)
        self.assertEqual(first_user.fetch_overall_leaderboard_position(), 1)

    def test_fetch_user_count(self):
        User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        User.objects.create(username='dGuy', email='d@abv.dg', password='123', score=122, role=self.base_role)
        User.objects.create(username='dGumasky', email='molly@abv.bg', password='123', score=122, role=self.base_role)
        User.objects.create(username='xdGumasky', email='xmolly@abv.bg', password='123', score=122, role=self.base_role)
        User.objects.create(username='dbrr', email='dd@abv.bg', password='123', score=121, role=self.base_role)

        self.assertEqual(User.fetch_user_count(), 5)


class RegisterViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')

    def test_register(self):
        # The user posts his username, email and password to the /accounts/register URL
        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'meredith@abv.bg'})
        # Should have successfully register the user and gave him a user token
        self.assertEqual(response.status_code, 201)
        self.assertTrue('user_token' in response.data)

    def test_register_existing_user_should_return_400(self):
        User.objects.create(email='that_part@abv.bg', password='123', username='ThatPart', role=self.base_role)

        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'that_part@abv.bg'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertIn('email already exists', ''.join(response.data['email']))

    def test_register_existing_username_should_return_400(self):
        User.objects.create(email='that_part@abv.bg', password='123', username='ThatPart', role=self.base_role)

        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'ThatPart',
                                                                               'password': 'mer19222',
                                                                               'email': 'TANKTNAK@abv.bg'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data)
        self.assertIn('username already exists', ''.join(response.data['username']))


class LoginViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='Base')

    def test_logging_in_valid(self):
        # There is a user account
        User.objects.create(email='that_part@abv.bg', password='123', role=self.base_role)
        # And we try logging in to it
        response: HttpResponse = self.client.post('/accounts/login/', data={'email': 'that_part@abv.bg',
                                                                            'password': '123'})
        self.assertEqual(response.status_code, 202)
        self.assertTrue('user_token' in response.data)

    def test_logging_in_invalid_email(self):
        # There is a user account
        User.objects.create(email='that_part@abv.bg', password='123', role=self.base_role)
        # And we try logging in to it
        response: HttpResponse = self.client.post('/accounts/login/', data={'email': 'INVALID_EMAIL',
                                                                            'password': '123'})

        self.assertEqual(response.status_code, 400)
        # the response should return an error that the email is invalid
        self.assertIn('error', response.data)
        self.assertIn('Invalid credentials', ''.join(response.data['error']))


class LeaderboardViewTest(APITestCase):
    def setUp(self):
        """
        Create users with expected positions
        """
        self.role = Role.objects.create(name='Basic')
        self.first_user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.role)
        self.second_user = User.objects.create(username='dGuy', email='d@abv.dg', password='123', score=122, role=self.role)
        self.second_user2 = User.objects.create(username='dGumasky', email='molly@abv.bg', password='123', score=122, role=self.role)
        self.second_user3 = User.objects.create(username='xdGumasky', email='xmolly@abv.bg', password='123', score=122, role=self.role)
        self.fifth_user = User.objects.create(username='dbrr', email='dd@abv.bg', password='123', score=121, role=self.role)

    def test_view_returns_expected_position(self):
        auth_token = 'Token {}'.format(self.first_user.auth_token.key)
        received_data = self.client.get('/challenges/selfLeaderboardPosition', HTTP_AUTHORIZATION=auth_token).data
        self.assertEqual(received_data['position'], 1)
        self.assertEqual(received_data['leaderboard_count'], 5)

    def test_view_returns_expected_last_position(self):
        auth_token = 'Token {}'.format(self.fifth_user.auth_token.key)
        received_data = self.client.get('/challenges/selfLeaderboardPosition', HTTP_AUTHORIZATION=auth_token).data

        self.assertEqual(received_data['position'], 5)
        self.assertEqual(received_data['leaderboard_count'], 5)

    def test_view_returns_expected_multiple_user_position(self):
        """ When multiple users have the same score and position, should return that position """
        auth_token = 'Token {}'.format(self.second_user3.auth_token.key)
        received_data = self.client.get('/challenges/selfLeaderboardPosition', HTTP_AUTHORIZATION=auth_token).data

        self.assertEqual(received_data['position'], 2)
        self.assertEqual(received_data['leaderboard_count'], 5)

    def test_get_leaderboard(self):
        """
        Should return a leaderboard with each user's position
        we expect each second_user* to be at 2nd place and the fifth user to be at fifth
        """
        expected_positions = {
            self.fifth_user.username: 5,
            self.second_user.username: 2,
            self.second_user2.username: 2,
            self.second_user3.username: 2,
            self.first_user.username: 1
        }
        auth_token = 'Token {}'.format(self.second_user3.auth_token.key)

        received_leaderboard = self.client.get('/challenges/getLeaderboard', HTTP_AUTHORIZATION=auth_token).data

        for lead in received_leaderboard:
            user_name = lead['name']
            self.assertEqual(lead['position'], expected_positions[user_name])


class UserDetailsViewTest(APITestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        self.auth_token = 'Token {}'.format(self.user.auth_token.key)

    def test_returns_expected_data(self):
        response = self.client.get(f'/accounts/user/{self.user.id}', HTTP_AUTHORIZATION=self.auth_token)
        expected_data = {'id': self.user.id, 'username': self.user.username, 'email': self.user.email,
                 'score': self.user.score,
                 'follower_count': self.user.followers.count(),
                 'role': {'id': self.user.role.id, 'name': self.user.role.name}}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_requires_authentication(self):
        response = self.client.get(f'/accounts/user/{self.user.id}')
        self.assertEqual(response.status_code, 401)
