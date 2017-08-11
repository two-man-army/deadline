import json
from collections import OrderedDict
from unittest import skip
from unittest.mock import MagicMock

from django.test import TestCase
from rest_framework.renderers import JSONRenderer

from challenges.models import Challenge, MainCategory, ChallengeDescription, SubCategory, User, \
    UserSubcategoryProficiency, Proficiency, Submission, Language
from challenges.serializers import MainCategorySerializer, SubCategorySerializer, LimitedChallengeSerializer
from challenges.tests.factories import ChallengeDescFactory, UserFactory, MainCategoryFactory
from challenges.tests.base import TestHelperMixin


class CategoryModelTest(TestCase):
    def setUp(self):
        self.c1 = MainCategory.objects.create(name='Test')
        self.sub1 = SubCategory(name='Unit', meta_category=self.c1)
        self.sub2 = SubCategory(name='Mock', meta_category=self.c1)
        self.sub3 = SubCategory(name='Patch', meta_category=self.c1)
        self.sub1.save();self.sub2.save();self.sub3.save()

    def test_relationships(self):
        """ The categories should be connected"""
        self.assertIn(self.sub1, self.c1.sub_categories.all())
        self.assertEqual(self.sub1.meta_category, self.c1)

    def test_serialize(self):
        """ the Category should show all its subcategories """
        expected_json = '{"name":"Test","sub_categories":["Unit","Mock","Patch"]}'
        received_data = JSONRenderer().render(MainCategorySerializer(self.c1).data)

        self.assertEqual(received_data.decode('utf-8'), expected_json)


class CategoryViewTest(TestCase):
    def setUp(self):
        self.c1 = MainCategoryFactory()
        self.c2 = MainCategoryFactory()
        self.c3 = MainCategoryFactory()
        self.c4 = MainCategoryFactory()
        self.c5 = MainCategoryFactory()

    def test_view_all_should_return_all_categories(self):
        response = self.client.get('/challenges/categories/all')
        self.assertEqual(response.data, MainCategorySerializer([self.c1, self.c2, self.c3, self.c4, self.c5],
                                                               many=True).data)


class SubCategoryModelTest(TestCase, TestHelperMixin):
    def setUp(self):
        self.c1 = MainCategory.objects.create(name='Test')
        self.sub1 = SubCategory.objects.create(name='Unit', meta_category=self.c1)
        self.sub2 = SubCategory.objects.create(name='Mock', meta_category=self.c1)
        self.sub3 = SubCategory.objects.create(name='Patch', meta_category=self.c1)
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.create_user_and_auth_token()
        self.sample_desc = ChallengeDescFactory()

    # @skip  # serialization does not currently work correctly as we want to return max score for challenge
    def test_serialize(self):
        """ Ths Subcategory should show all its challenges"""
        self.subcategory_progress = UserSubcategoryProficiency.objects.filter(subcategory=self.sub1,
                                                                              user=self.auth_user).first()
        print(self.sub1.id)
        c = Challenge.objects.create(name='TestThis', difficulty=5, score=10, description=self.sample_desc,
                                     test_case_count=5, category=self.sub1)
        c.save()
        python_language = Language.objects.create(name="Python")
        self.subcategory_progress.user_score = 5
        self.subcategory_progress.save()
        self.sub1.max_score = c.score
        req_mock = MagicMock(user=self.auth_user)
        expected_data = {'name': 'Unit',
                         'challenges': LimitedChallengeSerializer(many=True).to_representation(self.sub1.challenges.all()),
                         'max_score': self.sub1.max_score,
                         'proficiency': {'name': self.subcategory_progress.proficiency.name,
                                         'user_score': self.subcategory_progress.user_score}
                         }

        received_data = SubCategorySerializer(self.sub1, context={'request': req_mock}).data

        self.assertEqual(received_data, expected_data)

    @skip  # need to find a better place for that logic, AppConfig does not do the job as it runs before migrations
    def test_subcategory_max_score_is_updated(self):
        """
        Test if the SubCategory's max score is updated on server startup.
        This is done to capture the fact that sometimes we'll have new challenges added or removed and
        it needs to reflex the max score in a subcategory
        """
        from django.apps import apps
        c1 = Challenge(name='Sub1', difficulty=5, score=200, description=ChallengeDescFactory(),
                      test_case_count=5, category=self.sub1)
        c2 = Challenge(name='Sub1_2', difficulty=5, score=200, description=ChallengeDescFactory(),
                      test_case_count=5, category=self.sub1)
        c3 = Challenge(name='Sub2', difficulty=5, score=200, description=ChallengeDescFactory(),
                       test_case_count=5, category=self.sub2)
        c1.save(); c2.save(); c3.save()

        challenge_config = apps.get_app_config('challenges')
        challenge_config.ready()

        self.sub1.refresh_from_db()
        self.sub2.refresh_from_db()
        self.sub3.refresh_from_db()
        self.assertEqual(self.sub1.max_score, 400)
        self.assertEqual(self.sub2.max_score, 200)
        self.assertEqual(self.sub3.max_score, 0)


class SubCategoryViewTest(TestCase, TestHelperMixin):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.c1 = MainCategory(name='Test')
        self.c1.save()
        self.sub1 = SubCategory(name='Unit Tests', meta_category=self.c1)
        self.sub1.save()
        self.create_user_and_auth_token()

        self.c = Challenge.objects.create(name='TestThis', difficulty=5, score=10, description=self.sample_desc, test_case_count=5, category=self.sub1)

    def test_view_subcategory_detail_should_show(self):
        self.c.user_max_score = 0
        ser = LimitedChallengeSerializer(data=[self.c], many=True); ser.is_valid()
        # Should attach the user's proficiency in the subcategory to the data
        subcat_prof = self.auth_user.fetch_subcategory_proficiency(self.sub1.id)
        subcat_prof.user_score = 5
        subcat_prof.save()
        prof_obj = OrderedDict()
        prof_obj['name'] = 'starter'
        prof_obj['user_score'] = 5
        expected_data = {"name": self.sub1.name, "challenges": ser.data, 'max_score': self.sub1.max_score, 'proficiency': prof_obj}

        response = self.client.get('/challenges/subcategories/{}'.format(self.sub1.name),
                                   HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_view_unauthorized_should_401(self):
        response = self.client.get('/challenges/subcategories/{}'.format(self.sub1.name))
        self.assertEqual(response.status_code, 401)

    def test_view_invalid_subcategory_should_404(self):
        response = self.client.get('/challenges/subcategories/{}'.format('" OR 1=1;'),
                                   HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)


