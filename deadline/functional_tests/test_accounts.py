import re

from django.test import TestCase
from django.http import HttpResponse
from django.core import mail


class TestAccounts(TestCase):
    def test_register(self):
        # The user posts his username, email and password to the /accounts/register URL
        email_address = 'meredith@abv.bg'
        response: HttpResponse = self.client.post('/accounts/register', data={'username': 'Meredith',
                                                  'password': 'mer192',
                                                  'email': email_address})

        # Should have successfully register the user and gave him a user token
        self.assertEqual(response.status_code, 201)
        self.assertTrue(hasattr(response, 'user_token'))
