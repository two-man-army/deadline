import json

from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from unittest import skip
from challenges.models import Challenge, MainCategory, ChallengeDescription, SubCategory, User
from challenges.serializers import MainCategorySerializer, SubCategorySerializer, LimitedChallengeSerializer
from challenges.tests.factories import ChallengeDescFactory


class CategoryModelTest(TestCase):
    def setUp(self):
        self.c1 = MainCategory(name='Test')
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
        self.c1 = MainCategory(name='Test')
        self.c2 = MainCategory(name='Data')
        self.c3 = MainCategory(name='Structures')
        self.c4 = MainCategory(name='Rustlang')
        self.c5 = MainCategory(name='Others')
        self.c1.save();self.c2.save();self.c3.save();self.c4.save();self.c5.save()

    def test_view_all_should_return_all_categories(self):
        response = self.client.get('/challenges/categories/all')
        self.assertEqual(response.data, MainCategorySerializer([self.c1, self.c2, self.c3, self.c4, self.c5],
                                                               many=True).data)


class SubCategoryModelTest(TestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        self.c1 = MainCategory(name='Test')
        self.sub1 = SubCategory(name='Unit', meta_category=self.c1)
        self.sub2 = SubCategory(name='Mock', meta_category=self.c1)
        self.sub3 = SubCategory(name='Patch', meta_category=self.c1)
        self.sub1.save(); self.sub2.save(); self.sub3.save()

    @skip  # serialization does not currently work correctly as we want to return max score for challenge
    def test_serialize(self):
        """ Ths Subcategory should show all its challenges"""
        c = Challenge(name='TestThis', difficulty=5, score=10, description=self.sample_desc,
                      test_case_count=5, category=self.sub1)
        c.save()
        expected_json = '{"name":"Unit","challenges":[{"id":1,"name":"TestThis","difficulty":5.0,"score":10,"category":"Unit"}]}'
        received_data = JSONRenderer().render(SubCategorySerializer(self.sub1).data)
        self.assertEqual(received_data.decode('utf-8'), expected_json)

    def test_subcategory_max_score_is_updated(self):
        """
        The ChallengeConfig is called on every startup of the application
        Test if it updates the Submission XP
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


class SubCategoryViewTest(TestCase):
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.sample_desc.save()
        auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        auth_user.save()
        self.auth_token = 'Token {}'.format(auth_user.auth_token.key)
        self.c1 = MainCategory(name='Test')
        self.sub1 = SubCategory(name='Unit Tests', meta_category=self.c1)
        self.sub1.save()
        self.c = Challenge(name='TestThis', difficulty=5, score=10, description=self.sample_desc, test_case_count=5, category=self.sub1)
        self.c.save()

    def test_view_subcategory_detail_should_show(self):
        response = self.client.get('/challenges/subcategories/{}'.format(self.sub1.name),
                                   HTTP_AUTHORIZATION=self.auth_token)
        self.c.user_max_score = 0
        ser = LimitedChallengeSerializer(data=[self.c], many=True); ser.is_valid()
        expected_data = {"name": self.sub1.name, "challenges": ser.data, 'max_score': self.sub1.max_score}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_view_unauthorized_should_401(self):
        response = self.client.get('/challenges/subcategories/{}'.format(self.sub1.name))
        self.assertEqual(response.status_code, 401)

    def test_view_invalid_subcategory_should_404(self):
        response = self.client.get('/challenges/subcategories/{}'.format('" OR 1=1;'),
                                   HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)
