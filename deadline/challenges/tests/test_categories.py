from django.test import TestCase
from rest_framework.renderers import JSONRenderer

from challenges.models import ChallengeCategory, SubCategory
from challenges.serializers import ChallengeCategorySerializer


class CategoryModelTest(TestCase):
    def setUp(self):
        self.c1 = ChallengeCategory(name='Test')
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
        received_data = JSONRenderer().render(ChallengeCategorySerializer(self.c1).data)

        self.assertEqual(received_data.decode('utf-8'), expected_json)

