from django.test import TestCase

from accounts.models import Role, User, UserPersonalDetails
from accounts.serializers import UserPersonalDetailsSerializer, UserProfileSerializer
from challenges.tests.factories import UserFactory


class UserProfileSerializerTest(TestCase):
    def setUp(self):
        self.base_role = Role.objects.create(name='User')
        self.user = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123,
                                        role=self.base_role)
        self.profile_user = User.objects.create(username='Ben Foster', email='ben@abv.bg', password='123', score=123,
                                                role=self.base_role)
        # create two followers
        UserFactory().follow(self.profile_user)
        UserFactory().follow(self.profile_user)
        self.user.follow(self.profile_user)
        self.profile_user.follow(self.user)
        self.auth_token = 'Token {}'.format(self.user.auth_token.key)
        self.create_profile_user_details()

    def create_profile_user_details(self):
        self.about = 'I like riding tutrles'
        self.country = 'Spain'
        self.city = 'Madrid'
        self.school = 'West School of Hard Knocks'
        self.school_major = 'hard Knocking'
        self.job_title = ''
        self.job_company = ''
        self.personal_website = 'http://still.com'
        self.interests = ['mountain biking', 'mountain climbing']
        self.facebook_profile = 'Easy'
        self.linkedin_profile = ''
        self.github_profile = 'Enether'
        self.twitter_profile = ''
        UserPersonalDetails.objects.create(user_id=self.profile_user.id, about=self.about, country=self.country,
                                           city=self.city, school=self.school, school_major=self.school_major,
                                           job_title=self.job_title, job_company=self.job_company,
                                           personal_website=self.personal_website, interests=self.interests,
                                           facebook_profile=self.facebook_profile,
                                           linkedin_profile=self.linkedin_profile,
                                           github_profile=self.github_profile,
                                           twitter_profile=self.twitter_profile)

    def test_returns_expected_data(self):
        expected_data = {
            'following': True,  # self.user is following him
            'following_count': self.profile_user.users_followed.count(),
            'followers_count': self.profile_user.followers.count(),
            'registered_on': self.profile_user.created_at.isoformat(),
            "user_details": UserPersonalDetailsSerializer(instance=self.profile_user.personal_details).data
        }
        received_data = UserProfileSerializer(instance=self.profile_user, context={'caller': self.user}).data
        self.assertEqual(received_data, expected_data)
