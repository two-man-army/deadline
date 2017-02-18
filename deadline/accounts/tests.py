from django.test import TestCase
from accounts.models import User


# Create your tests here.
class UserModelTest(TestCase):
    def test_user_register_creates_token(self):
        us = User.objects.create(username='fuckyou', email='me@abv.bg', password='123', confirm_email='123', score=123)
        self.assertTrue(hasattr(us, 'auth_token'))
        self.assertIsNotNone(us.auth_token)