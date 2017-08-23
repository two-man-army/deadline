from unittest.mock import patch

from rest_framework.test import APITestCase

from challenges.tests.base import TestHelperMixin
from challenges.tests.factories import UserFactory
from private_chat.constants import PMS_PER_QUERY
from private_chat.models import Dialog, Message
from private_chat.serializers import MessageSerializer


class PreviousMessageListViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.first_user = UserFactory()
        self.first_us_token = f'Token {self.first_user.auth_token.key}'
        self.second_user = UserFactory()
        self.dialog = Dialog.objects.create(owner=self.auth_user, opponent=self.second_user)
        self.auth_us_messages = [Message.objects.create(text='whatup', sender=self.auth_user, dialog=self.dialog)
                                 for _ in range(5)]

    @patch('private_chat.views.Message.fetch_messages_from_dialog_created_before')
    def test_returns_messages(self, mock_fetch):
        before_pm = self.auth_us_messages[-1]
        expected_data = MessageSerializer(instance=self.auth_us_messages[:-1], many=True).data
        mock_fetch.return_value = self.auth_us_messages[:-1]
        url = f'/chat/messages?conversation_token={self.dialog.owner_token}&before_pm={before_pm.id}'

        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['messages'], expected_data)
        mock_fetch.assert_called_once_with(message=before_pm, message_count=PMS_PER_QUERY)

    def test_invalid_message_id_returns_400(self):
        url = f'/chat/messages?conversation_token={self.dialog.owner_token}&before_pm=111'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 400)

    def test_invalid_conversation_token_returns_400(self):
        before_pm = self.auth_us_messages[-1]
        url = f'/chat/messages?conversation_token=blablbal&before_pm={before_pm.id}'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 400)

    def test_user_not_in_dialog_returns_400(self):
        """
        Even if he has the correct conversation token, a user who does not participate in the
        dialog should not be able to fetch it
        """
        before_pm = self.auth_us_messages[-1]
        url = f'/chat/messages?conversation_token={self.dialog.owner_token}&before_pm={before_pm.id}'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.first_us_token)

        self.assertEqual(response.status_code, 400)

    def test_requires_authentication(self):
        before_pm = self.auth_us_messages[-1]
        url = f'/chat/messages?conversation_token={self.dialog.owner_token}&before_pm={before_pm.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
