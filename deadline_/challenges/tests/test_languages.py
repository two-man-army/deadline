from rest_framework.test import APITestCase

from accounts.models import User
from challenges.models import Language
from challenges.serializers import LanguageSerializer
from challenges.tests.base import TestHelperMixin


class LanguageViewTest(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.php = Language.objects.create(name="Php")

    def test_retrieve_lang(self):
        response = self.client.get(path='/challenges/languages/Php', HTTP_AUTHORIZATION=self.auth_token)
        ser = LanguageSerializer(self.php)
        expected_data = ser.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_retrieve_lang_ignores_case(self):
        response = self.client.get(path='/challenges/languages/PhP', HTTP_AUTHORIZATION=self.auth_token)
        ser = LanguageSerializer(self.php)
        expected_data = ser.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    def test_retrieve_non_existing_lang_should_404(self):
        response = self.client.get(path='/challenges/languages/elixir', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 404)
