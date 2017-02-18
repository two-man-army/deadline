from django.test import TestCase
from django.utils.six import BytesIO
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
        expected_json = '{"username":"SomeGuy","email":"me@abv.bg","password":"123","score":123}'

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
        self.assertEqual(deser_user.password, '123')
        self.assertEqual(deser_user.score, 123)