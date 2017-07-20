from random import randint
from unittest.mock import MagicMock

from django.test import TestCase
from unittest import TestCase as unittest_TestCase
from unittest.mock import MagicMock
from rest_framework.response import Response

from challenges.models import MainCategory, SubCategory
from errors import FetchError
from helpers import fetch_models_by_pks
from decorators import fetch_models, enforce_forbidden_fields
from challenges.tests.factories import MainCategoryFactory, SubCategoryFactory
from views import BaseManageView


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


class EnforceForbiddenFieldsDecoratorTest(TestCase):
    def setUp(self):
        class Tank:
            forbidden_fields = ('gucci_jacket', 'secured')

            @enforce_forbidden_fields
            def get(self, request, *args, **kwargs):
                return request

        self.Tank = Tank

    def test_returns_400_if_forbidden_field_is_present(self):
        request_object = MagicMock(data={'gucci_jacket': '150 stack it'})
        response = self.Tank().get(request_object)
        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'gucci_jacket is a forbidden field in the request data!')

    def test_raises_exception_if_forbidden_fields_not_defined(self):
        delattr(self.Tank, 'forbidden_fields')
        request_object = MagicMock(data={'gucci_jacket': '150 stack it'})
        with self.assertRaises(Exception):
            self.Tank().get(request_object)

    def test_raises_exception_if_forbidden_fields_are_not_iterable(self):
        self.Tank.forbidden_fields = 10
        request_object = MagicMock(data={'gucci_jacket': '150 stack it'})
        with self.assertRaises(Exception):
            self.Tank().get(request_object)

    def test_does_not_do_anything_if_no_field_is_present(self):
        request_object = MagicMock(data={'non_gucci_jacket': '-150 pay it'})
        request = self.Tank().get(request_object)
        self.assertEqual(request_object, request)


class BaseManageViewTests(unittest_TestCase):
    def test_raises_error_when_no_views_by_method_defined(self):
        with self.assertRaises(Exception):
            BaseManageView().dispatch(None)

    def test_calls_function_on_defined_method(self):
        inner_function_mock = MagicMock()
        inner_function_mock.return_value = 14
        mock = MagicMock()
        mock.return_value = inner_function_mock
        BaseManageView.VIEWS_BY_METHOD = {
            'GET': mock
        }
        request_mock = MagicMock(method='GET')
        result = BaseManageView().dispatch(request_mock)

        mock.assert_called_once_with()
        inner_function_mock.assert_called_once_with(request_mock)
        self.assertEqual(result, 14)

    def test_returns_404_exception_if_method_not_defined(self):
        BaseManageView.VIEWS_BY_METHOD = {
            'GET': None
        }
        request_mock = MagicMock(method='PUT')
        response = BaseManageView().dispatch(request_mock)

        self.assertTrue(isinstance(response, Response))
        self.assertEqual(response.status_code, 404)

