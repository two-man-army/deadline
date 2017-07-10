from random import randint

from django.test import TestCase

from challenges.models import MainCategory, SubCategory
from errors import FetchError
from helpers import fetch_models_by_pks
from challenges.tests.factories import MainCategoryFactory, SubCategoryFactory


class FetchModelsTest(TestCase):
    def setUp(self):
        # create some models
        self.main_cat = MainCategoryFactory()
        self.subcat = SubCategoryFactory()

    def test_fetches_instances_successfully(self):
        expected_results = [self.main_cat, self.subcat]
        received_results = fetch_models_by_pks({
            MainCategory: self.main_cat.id,
            SubCategory: self.subcat.id
        })
        self.assertTrue(expected_results, received_results)

    def test_fetches_FetchError_on_incorrect_id(self):
        with self.assertRaises(FetchError):
            received_results = fetch_models_by_pks({
                MainCategory: 200,
                SubCategory: self.subcat.id
            })

    def test_fetches_in_correct_order(self):
        """ test that the order in which we receive the models is that in which we sent them """
        for i in range(20):
            # pick which one is first
            main_cat_num = randint(0, 1)
            sub_cat_num = 0 if main_cat_num == 1 else 1
            expected_results = [None, None]
            expected_results[sub_cat_num] = self.subcat
            expected_results[main_cat_num] = self.main_cat
            received_results = fetch_models_by_pks({
                instance.__class__: instance.id for instance in expected_results
            })

            self.assertEqual(expected_results, received_results)
