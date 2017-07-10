from random import randint
from unittest.mock import MagicMock

from django.test import TestCase
from rest_framework.response import Response

from challenges.models import MainCategory, SubCategory
from errors import FetchError
from helpers import fetch_models_by_pks
from decorators import fetch_models
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


class FetchModelsDecoratorTest(TestCase):
    def setUp(self):
        class Tank:
            model_classes = (MainCategory, SubCategory)
            main_class = SubCategory

            @fetch_models
            def get(self, request, main_cat, sub_cat, *args, **kwargs):
                return request, main_cat, sub_cat
        self.Tank = Tank
        self.main_cat = MainCategoryFactory()
        self.sub_cat = SubCategoryFactory()

    def test_attaches_models(self):
        """ Also asserts that we send back the results from our function """
        f_instance = self.Tank()
        _, main_cat, sub_cat = f_instance.get(0, main_cat_pk=self.main_cat.id, subcat_pk=self.sub_cat.id)
        self.assertEqual(self.main_cat, main_cat)
        self.assertEqual(self.sub_cat, sub_cat)

    def test_returns_404__response_on_unsuccessful_fetch(self):
        f_instance = self.Tank()
        response = f_instance.get(0, main_cat_pk=200, subcat_pk=self.sub_cat.id)
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'MainCategory with ID 200 does not exist.')

    def test_raises_exception_on_more_pks_sent_than_classes_defined(self):
        """ As we have two model classes defined, sending three or one PKs should raise an exception"""
        f_instance = self.Tank()
        with self.assertRaises(Exception):
            f_instance.get(0, main_cat_pk=self.main_cat.id, subcat_pk=self.sub_cat.id, tank_pk=3)
        with self.assertRaises(Exception):
            f_instance.get(0, main_cat_pk=self.main_cat.id, )

    def test_raises_exception_if_model_classes_not_defined(self):
        delattr(self.Tank, 'model_classes')
        f_instance = self.Tank()

        with self.assertRaises(Exception):
            f_instance.get(0, main_cat_pk=self.main_cat.id, subcat_pk=self.sub_cat.id)

    def test_raises_exception_if_model_classes_not_iterable(self):
        self.Tank.model_classes = 2
        f_instance = self.Tank()

        with self.assertRaises(Exception):
            f_instance.get(0, main_cat_pk=self.main_cat.id, subcat_pk=self.sub_cat.id)

    def test_calls_permissions_and_returns_403_if_permission_returns_false(self):
        # TODO: Might want to test that its called as we want it
        self.Tank.permission_classes = (MagicMock(has_object_permission = lambda x, y, z: False), )
        f_instance = self.Tank()

        response = f_instance.get(0, main_cat_pk=self.main_cat.id, subcat_pk=self.sub_cat.id)
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_code, 403)
