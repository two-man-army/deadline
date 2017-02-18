from django.test import TestCase
from django.utils.six import BytesIO
from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from accounts.models import User
from accounts.serializers import UserSerializer


# Create your tests here.
class UserModelTest(TestCase):
    def test_user_register_creates_token(self):
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
        self.assertTrue(hasattr(us, 'auth_token'))
        self.assertIsNotNone(us.auth_token)

    def test_serialization(self):
        """ Should convert a user object to a json """
        us = User.objects.create(username='SomeGuy', email='me@abv.bg', password='123', score=123)
        # password should be hashed
        expected_json = '{"username":"SomeGuy","email":"me@abv.bg","password":"%s","score":123}' % (us.password)

        content = JSONRenderer().render(UserSerializer(us).data)
        self.assertEqual(content.decode('utf-8'), expected_json)

    def test_deserialization(self):
        expected_json = b'{"username":"SomeGuy","email":"me@abv.bg","password":"123","score":123}'

        data = JSONParser().parse(BytesIO(expected_json))
        serializer = UserSerializer(data=data)

        serializer.is_valid()
        deser_user = serializer.save()

        self.assertIsInstance(deser_user, User)
        self.assertEqual(deser_user.username, 'SomeGuy')
        self.assertEqual(deser_user.email, 'me@abv.bg')
        self.assertNotEqual(deser_user.password, '123')  # should be hashed!
        self.assertEqual(deser_user.score, 123)


class RegisterViewTest(APITestCase):
    def test_register(self):
        # The user posts his username, email and password to the /accounts/register URL
        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'meredith@abv.bg'})
        # Should have successfully register the user and gave him a user token
        self.assertEqual(response.status_code, 201)
        self.assertTrue('user_token' in response.data)

    def test_register_existing_user_should_return_400(self):
        User.objects.create(email='that_part@abv.bg', password='123', username='ThatPart')

        response: HttpResponse = self.client.post('/accounts/register/', data={'username': 'Meredith',
                                                                               'password': 'mer19222',
                                                                               'email': 'that_part@abv.bg'})
        # Should have successfully register the user and gave him a user token
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertIn('email already exists', ''.join(response.data['email']))

class LoginViewTest(APITestCase):
    def test_logging_in_the_system(self):
        # There is a user account
        User.objects.create(email='that_part@abv.bg', password='123')
        # And we try logging in to it
        response: HttpResponse = self.client.post('/accounts/login/', data={'email': 'that_part@abv.bg',
                                                                            'password': '123'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('user_token' in response.data)
