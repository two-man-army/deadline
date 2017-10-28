import re
from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock

import jwt
from django.http import HttpResponse
from django.test import TestCase
from django.utils.six import BytesIO
from rest_framework.test import APITestCase
from rest_framework.parsers import JSONParser

from accounts.constants import (
    NOTIFICATION_SECRET_KEY, FACEBOOK_PROFILE_REGEX, TWITTER_PROFILE_REGEX,
    GITHUB_PROFILE_REGEX, LINKEDIN_PROFILE_REGEX
)
from accounts.errors import UserAlreadyFollowedError, UserNotFollowedError
from accounts.helpers import generate_notification_token
from accounts.models import User, Role, UserPersonalDetails
from accounts.serializers import UserSerializer
from challenges.tests.factories import UserFactory, ChallengeDescFactory
from challenges.models import (Challenge, Submission, Language, SubmissionVote, Proficiency,
                               UserSubcategoryProficiency, SubCategory, MainCategory)
from social.constants import NW_ITEM_TEXT_POST
from social.models.newsfeed_item import NewsfeedItem
from social.models.notification import Notification

# TODO: Separate tests in a /tests/ directory


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

    @patch('accounts.models.generate_notification_token')
    def test_user_register_creates_notification_token(self, gen_notif_mock):
        gen_notif_mock.return_value = 'deadshot_brr_ak_make_your_head_rock'

        new_user = User.objects.create(username='user3', password='123', email='user3@abv.bg', score=123, role=self.base_role)

        self.assertIsNotNone(new_user.notification_token)
        self.assertEqual(new_user.notification_token, 'deadshot_brr_ak_make_your_head_rock')
        gen_notif_mock.assert_called_once()

    def test_user_register_assigns_default_user_role(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        self.assertEqual(us.role, self.base_role)

    def test_user_register_creates_user_subcategory_proficiency(self):
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

    def test_follow_creates_notification(self):
        user_who_gets_followed = User.objects.create(username='SomeFollowee', email='me@abv.bg', password='123', score=123, role=self.base_role)
        follower = User.objects.create(username='SomeGuy', email='follower@abv.bg', password='123', score=123, role=self.base_role)

        follower.follow(user_who_gets_followed)

        self.assertEqual(Notification.objects.filter(recipient=user_who_gets_followed).count(), 1)

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
        self.set_up_fetch_unsuccessful_challenge_attempts_count_tests()
        s = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                      code='a')

        sv1 = SubmissionVote.objects.create(author=self.auth_user, submission=s, is_upvote=False)

        received_vote = self.auth_user.get_vote_for_submission(submission_id=s.id)
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

    def test_fetch_count_of_solved_challenges_for_subcategory(self):
        from challenges.models import Challenge, Submission, SubCategory, MainCategory, Language
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)

        python_language = Language.objects.create(name="Python")
        challenge_cat = MainCategory.objects.create(name='Tests')
        sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        challenge = Challenge.objects.create(name='Hello', difficulty=5, score=10, description=ChallengeDescFactory(),
                                             test_case_count=3, category=sub_cat)
        Submission.objects.create(language=python_language, challenge=challenge, pending=False,
                                  author=us, result_score=challenge.score, code="")

        expected_count = 1
        received_count = us.fetch_count_of_solved_challenges_for_subcategory(sub_cat)
        self.assertEqual(expected_count, received_count)

    def test_fetch_count_of_solved_challenges_for_subcategory_returns_0_for_none_solved(self):
        from challenges.models import Challenge, Submission, SubCategory, MainCategory, Language
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)

        Language.objects.create(name="Python")
        challenge_cat = MainCategory.objects.create(name='Tests')
        sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        Challenge.objects.create(name='Hello', difficulty=5, score=10, description=ChallengeDescFactory(),
                                 test_case_count=3, category=sub_cat)

        expected_count = 0
        received_count = us.fetch_count_of_solved_challenges_for_subcategory(sub_cat)
        self.assertEqual(expected_count, received_count)

    def test_fetch_count_of_solved_challenges_for_subcategory_returns_0_for_one_partially_solved(self):
        from challenges.models import Challenge, Submission, SubCategory, MainCategory, Language
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)

        python_language = Language.objects.create(name="Python")
        challenge_cat = MainCategory.objects.create(name='Tests')
        sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        challenge = Challenge.objects.create(name='Hello', difficulty=5, score=10, description=ChallengeDescFactory(),
                                             test_case_count=3, category=sub_cat)

        Submission.objects.create(language=python_language, challenge=challenge,
                                  author=us, result_score=challenge.score-1, code="")

        expected_count = 0
        received_count = us.fetch_count_of_solved_challenges_for_subcategory(sub_cat)
        self.assertEqual(expected_count, received_count)

    def test_fetch_count_of_solved_challenges_for_subcategory_returns_appropriate_number_for_mixed_submissions(self):
        from challenges.models import Challenge, Submission, SubCategory, MainCategory, Language
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)

        python_language = Language.objects.create(name="Python")
        challenge_cat = MainCategory.objects.create(name='Tests')
        sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        # Create 10 challenges, the first 3 of which have passing submissions, others incomplete
        for i in range(10):
            challenge = Challenge.objects.create(name=f'Hello{i}', difficulty=5, score=10,
                                                 description=ChallengeDescFactory(), test_case_count=3, category=sub_cat)
            if i < 3:
                # Create one passing submission and some failing
                Submission.objects.create(language=python_language, challenge=challenge, pending=False,
                                          author=us, result_score=challenge.score-1, code="")
                Submission.objects.create(language=python_language, challenge=challenge, pending=False,
                                          author=us, result_score=challenge.score, code="")
                Submission.objects.create(language=python_language, challenge=challenge, pending=True,
                                          author=us, result_score=challenge.score, code="")
            else:
                # Create multiple non passing
                Submission.objects.create(language=python_language, challenge=challenge, pending=False,
                                          author=us, result_score=challenge.score-1, code="")
                Submission.objects.create(language=python_language, challenge=challenge, pending=False,
                                          author=us, result_score=0, code="")
                Submission.objects.create(language=python_language, challenge=challenge, pending=False,
                                          author=us, result_score=2, code="")

        expected_count = 3
        received_count = us.fetch_count_of_solved_challenges_for_subcategory(sub_cat)
        self.assertEqual(expected_count, received_count)

    def set_up_fetch_unsuccessful_challenge_attempts_count_tests(self):
        """ Create a User, Language and a Challenge"""
        self.auth_user: User = UserFactory()
        self.python_language = Language.objects.create(name="Python")
        self.challenge_cat = MainCategory.objects.create(name='Tests'); self.challenge_cat.save()
        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=self.challenge_cat)
        self.challenge = Challenge.objects.create(name='Hello', difficulty=5, score=10, description=ChallengeDescFactory(),
                                             test_case_count=3, category=self.sub_cat)

    def test_fetch_unsuccessful_challenge_attempts_count(self):
        self.set_up_fetch_unsuccessful_challenge_attempts_count_tests()
        # create 3 unsuccessful submissions and one successful
        for i in range(3):
            Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                      pending=False, result_score=1)
        # one successful submission
        Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                  pending=False, result_score=self.challenge.score)

        unsuc_count = self.auth_user.fetch_unsuccessful_challenge_attempts_count(self.challenge)
        self.assertEqual(unsuc_count, 3)

    def test_fetch_unsuccessful_challenge_attempts_count_ignores_other_challenge_submissions(self):
        self.set_up_fetch_unsuccessful_challenge_attempts_count_tests()
        # create 10 unsuccesful submissions for another challenge
        other_challenge = Challenge.objects.create(name='Ev', difficulty=5, score=200, description=ChallengeDescFactory()
                                                   , test_case_count=3, category=self.sub_cat)
        for i in range(10):
            Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=other_challenge,
                                      pending=False, result_score=1)

        # create 3 unsuccessful submissions and one successful
        for i in range(3):
            Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                      pending=False, result_score=1)
        # one successful submission
        Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                  pending=False, result_score=self.challenge.score)

        unsuc_count = self.auth_user.fetch_unsuccessful_challenge_attempts_count(self.challenge)
        self.assertEqual(unsuc_count, 3)

    def fetch_unsuccessful_challenge_attempts_count_all_successful_should_return_0(self):
        self.set_up_fetch_unsuccessful_challenge_attempts_count_tests()
        # create 3 successful submissions and one successful
        for i in range(3):
            Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                      pending=False, result_score=self.challenge.score)

        unsuc_count = self.auth_user.fetch_unsuccessful_challenge_attempts_count(self.challenge)
        self.assertEqual(unsuc_count, 0)

    def test_fetch_unsuccessful_challenge_attempts_count_ignores_successful_attempts(self):
        self.set_up_fetch_unsuccessful_challenge_attempts_count_tests()
        # create 3 successful submissions and one successful
        for i in range(3):
            Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                      pending=False, result_score=self.challenge.score)
        # create 2 unsuccessful
        for i in range(2):
            Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                      pending=False, result_score=self.challenge.score-1)

        unsuc_count = self.auth_user.fetch_unsuccessful_challenge_attempts_count(self.challenge)
        self.assertEqual(unsuc_count, 2)

    def test_fetch_unsuccessful_challenge_attempts_count_ignores_pending_submissions(self):
        """
        As Pending denoted if the Submission is still being graded,
            a pending submission should not count towards an unsuccessful attempt
        """
        self.set_up_fetch_unsuccessful_challenge_attempts_count_tests()

        # one successful, one unsuccessful
        Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                  pending=False, result_score=self.challenge.score)
        Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                  pending=False, result_score=self.challenge.score-1)
        # 10 unsuccessful which are still pending
        for i in range(10):
            Submission.objects.create(language=self.python_language, author=self.auth_user, challenge=self.challenge,
                                      pending=True, result_score=self.challenge.score-1)

        unsuc_count = self.auth_user.fetch_unsuccessful_challenge_attempts_count(self.challenge)
        self.assertEqual(unsuc_count, 1)

    @patch('accounts.models.generate_notification_token')
    @patch('accounts.models.User.notification_token_is_expired')
    def test_refresh_notification_token(self, mock_is_exp, mock_gen):
        mock_is_exp.return_value = True
        mock_gen.return_value = 'token :)'

        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.refresh_notification_token()

        mock_is_exp.assert_called_once()
        mock_gen.assert_called_with(us)
        self.assertEqual(len(mock_gen.mock_calls), 2)  # called once on registration
        self.assertEqual(us.notification_token, 'token :)')

    @patch('accounts.models.generate_notification_token')
    @patch('accounts.models.User.notification_token_is_expired')
    def test_refresh_notification_token_should_not_reset_if_not_expired(self, mock_is_exp, mock_gen):
        mock_is_exp.return_value = False
        mock_gen.return_value = 'token :)'

        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        with self.assertRaises(Exception):
            us.refresh_notification_token()

    @patch('accounts.models.generate_notification_token')
    @patch('accounts.models.User.notification_token_is_expired')
    def test_refresh_notification_token_non_expired_token_should_be_reset_with_force(self, mock_is_exp, mock_gen):
        mock_is_exp.return_value = False
        mock_gen.return_value = 'token :)'

        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.refresh_notification_token(force=True)

        mock_gen.assert_called_with(us)
        self.assertEqual(len(mock_gen.mock_calls), 2)  # called once on registration as well
        self.assertEqual(us.notification_token, 'token :)')

    @patch('accounts.models.User.notification_token_is_expired')
    def test_token_is_valid(self, mock_is_exp):
        mock_is_exp.return_value = False
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.notification_token = 'h'

        self.assertTrue(us.notification_token_is_valid('h'))
        self.assertFalse(us.notification_token_is_valid('m'))

    @patch('accounts.models.User.notification_token_is_expired')
    def test_token_is_valid_expired_token(self, mock_is_exp):
        mock_is_exp.return_value = True
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        us.notification_token = 'h'

        self.assertFalse(us.notification_token_is_valid('h'))

    def test_notification_token_is_expired(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        expiry_date = datetime.utcnow() - timedelta(minutes=1)
        notification_token = jwt.encode({'exp': expiry_date, 'username': us.username}, NOTIFICATION_SECRET_KEY).decode("utf-8")

        us.notification_token = notification_token

        self.assertTrue(us.notification_token_is_expired())

    def test_notification_token_is_expired_returns_false_when_not_exp(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123, role=self.base_role)
        expiry_date = datetime.utcnow() + timedelta(minutes=1)
        notification_token = jwt.encode({'exp': expiry_date, 'username': us.username}, NOTIFICATION_SECRET_KEY).decode("utf-8")

        us.notification_token = notification_token

        self.assertFalse(us.notification_token_is_expired())


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
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserPersonalDetails.objects.count(), 1)

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


class HelpersTest(TestCase):
    @patch('accounts.helpers.NOTIFICATION_TOKEN_EXPIRY_MINUTES', 20)
    @patch('accounts.helpers.jwt.encode')
    @patch('accounts.helpers.get_utc_time')
    def test_generate_notification_token(self, mock_utc_time, mock_jwt_encode):
        utc_time = datetime.utcnow()
        mock_utc_time.return_value = utc_time
        expected_expiry_date = utc_time + timedelta(minutes=20)
        mock_jwt_encode.return_value = MagicMock(decode=lambda x: 'chrissy')

        notif_token = generate_notification_token(MagicMock(username='yo'))

        mock_jwt_encode.assert_called_once_with({'exp': expected_expiry_date, 'username': 'yo'}, NOTIFICATION_SECRET_KEY)
        self.assertEqual('chrissy', notif_token)


class RegexesTest(TestCase):
    def assertMatchesURL(self, match_regex, url):
        self.assertIsNotNone(re.match(match_regex, url),
                             msg=f'{url} did not match regex {match_regex}!')

    def assertDoesNotMatchURL(self, match_regex, url):
        self.assertIsNone(re.match(match_regex, url),
                          msg=f'{url} matched {match_regex}!')

    def test_facebook_profile_regex_matches_positives(self):
        valid_links = [
            'http://www.facebook.com/mypageusername?ref=hl',
            'facebook.com/mypageusername',
            'https://www.facebook.com/yourworldwithin/?hc_ref=ARTWAkSewGoStjGHFn1spDJc7YNtPHH570Ep9i5-FiVsGwcOH-Vqoz3tE8xZpEnXXlE&fref=nf'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(FACEBOOK_PROFILE_REGEX, valid_link)

    def test_facebook_profile_regex_matches_page_name(self):
        profile_name_by_link = {
            'http://www.facebook.com/mypageusername?ref=hl': 'mypageusername',
            'facebook.com/mypageusername': 'mypageusername',
            'https://www.facebook.com/yourworldwithin/?hc_ref=ARTWAkSewGoStjGHFn1spDJc7YNtPHH570Ep9i5-FiVsGwcOH-Vqoz3tE8xZpEnXXlE&fref=nf': 'yourworldwithin'
        }
        for link, profile_name in profile_name_by_link.items():
            extracted_page_name = re.match(FACEBOOK_PROFILE_REGEX, link).group('page_name')
            self.assertEqual(extracted_page_name, profile_name)

    def test_facebook_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'http://www.fасеbook.com/mypageusername',  # cyrillic characters in URL
            'https://www.facebook.co/mypageusername?ref=hl',
            'http://www.facebook.org/pages/Vanity-Url/12345678?ref=hl',
            'https://www.fb-page.com/pages/Vanity-Url/12345678?ref=hl',
            'https://www.facebook.com/heymelikey/photos/a.760078844002883.1073741828.759042127439888/1742633762414048/?type=3',
            'https://www.facebook.com/hnbot/posts/1514015915320351'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(FACEBOOK_PROFILE_REGEX, invalid_link)

    def test_twitter_profile_regex_matches_positives(self):
        valid_links = [
            'https://twitter.com/barackobama?lang=bgdDdas214913r_#qrfcDJAMBOXs\\\\\\\d',
            'https://twitter.com/EdubHipHop',
            'twitter.com/EdubHipHop?lang=bg'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(TWITTER_PROFILE_REGEX, valid_link)

    def test_twitter_profile_regex_matches_profile_name(self):
        profile_name_by_link = {
            'https://twitter.com/barackobama?lang=bgdDdas214913r_#qrfcDJAMBOXs\\\\\\\d': 'barackobama',
            'https://twitter.com/EdubHipHop': 'EdubHipHop',
            'twitter.com/EdubHipHop?lang=bg': 'EdubHipHop'
        }
        for link, profile_name in profile_name_by_link.items():
            extracted_page_name = re.match(TWITTER_PROFILE_REGEX, link).group('profile_name')
            self.assertEqual(extracted_page_name, profile_name)

    def test_twitter_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'https://twittеr.соm/EdubHipHop',  # cyrillic
            'twitter.co/EdubHipHop?lang=bg'
            'https://twtr.com/EdubHipHop?lang=bg'
            'https://twitter.com/EdubHipHop/status/761547917882695681'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(TWITTER_PROFILE_REGEX, invalid_link)

    def test_github_profile_regex_matches_positives(self):
        valid_links = [
            'www.github.com/Enether',
            'www.github.com/vgramov?te=334'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(GITHUB_PROFILE_REGEX, valid_link)

    def test_github_profile_regex_matches_profile_name(self):
        usernames_by_links = {
            'www.github.com/Enether': 'Enether',
            'www.github.com/vgramov?te=334': 'vgramov'
        }
        for link, username in usernames_by_links.items():
            extracted_page_name = re.match(GITHUB_PROFILE_REGEX, link).group('profile_name')
            self.assertEqual(extracted_page_name, username)

    def test_github_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'www.github.соm/Enether',  # cyrillic
            'www.github.co/vgramov?te=334'
            'www.github.com/vgramov/java_game'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(GITHUB_PROFILE_REGEX, invalid_link)

    def test_linkedin_profile_regex_matches_positives(self):
        valid_links = [
            'https://www.linkedin.com/in/williamhgates/',
            'www.linkedin.com/in/stanislavkozlovski?lang=bg',
            'www.linkedin.com/in/tank-mihailov-a52a1498/'
        ]
        for valid_link in valid_links:
            self.assertMatchesURL(LINKEDIN_PROFILE_REGEX, valid_link)

    def test_linkedin_profile_regex_matches_profile_name(self):
        usernames_by_links = {
            'https://www.linkedin.com/in/williamhgates/': 'williamhgates',
            'www.linkedin.com/in/stanislavkozlovski?lang=bg': 'stanislavkozlovski',
            'www.linkedin.com/in/tank-mihailov-a52a1498/': 'tank-mihailov-a52a1498'
        }
        for link, username in usernames_by_links.items():
            extracted_page_name = re.match(LINKEDIN_PROFILE_REGEX, link).group('profile_name')
            self.assertEqual(extracted_page_name, username)

    def test_linkedin_profile_regex_doesnt_match_invalid_urls(self):
        invalid_links = [
            'https://www.linkedin.com/company/deadline/',
            'www.linkedin.com/in//'
            'www.linkedin.com/tank-mihailov-a52a1498/'
        ]
        for invalid_link in invalid_links:
            self.assertDoesNotMatchURL(LINKEDIN_PROFILE_REGEX, invalid_link)
