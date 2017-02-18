import re

from rest_framework.test import APITestCase
from django.shortcuts import reverse
from django.http import HttpResponse

from accounts.models import User


class TestAccounts(APITestCase):
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
