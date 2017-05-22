from rest_framework.test import APITestCase

from accounts.models import User
from challenges.models import Language
from challenges.serializers import LanguageSerializer


class LanguageViewTest(APITestCase):
    def setUp(self):
        self.auth_user = User(username='123', password='123', email='123@abv.bg', score=123)
        self.auth_user.save()
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)
        self.php = Language.objects.create(name="Php")
        self.php.save()

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
