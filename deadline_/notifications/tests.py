from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.renderers import JSONRenderer

from challenges.tests.base import TestHelperMixin
from notifications.errors import NotificationAlreadyRead, OfflineRecipientError
from notifications.handlers import NotificationsHandler
from social.models import Notification
from social.serializers import NotificationSerializer


class NotificationsHandlerTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up(create_user=True)
        self.notification = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=self.challenge)

    def test_receive_message_functions(self):
        with patch('notifications.handlers.ws_connections', {self.notification.recipient_id: MagicMock()}):
            self.assertTrue(NotificationsHandler.receive_message(str(self.notification.id)))

    @patch('notifications.handlers.NotificationsHandler.validate_notification')
    def test_fetch_notification_returns_notif_and_calls_validate(self, mock_validate_notif):
        received_notif = NotificationsHandler.fetch_notification(self.notification.id)
        self.assertEqual(received_notif, self.notification)
        mock_validate_notif.assert_called_once_with(self.notification)

    def test_validate_validates_successfully(self):
        with patch('notifications.handlers.ws_connections', {self.notification.recipient_id: MagicMock(is_valid=True)}):
            NotificationsHandler.validate_notification(self.notification)

    def test_validate_raises_already_read_if_notif_read(self):
        self.notification.is_read = True
        self.notification.save()

        with self.assertRaises(NotificationAlreadyRead):
            NotificationsHandler.validate_notification(self.notification)

    def test_validate_OfflineRecipientError_if_recipient_not_in_ws_conns(self):
        with patch('notifications.handlers.ws_connections', {}):
            with self.assertRaises(OfflineRecipientError):
                NotificationsHandler.validate_notification(self.notification)

    def test_validate_OfflineRecipientError_if_recipient_cons_not_validated(self):
        ws_conn_mock = {self.notification.recipient_id: MagicMock(is_valid=False)}
        with patch('notifications.handlers.ws_connections', ws_conn_mock):
            with self.assertRaises(OfflineRecipientError):
                NotificationsHandler.validate_notification(self.notification)

    def test_build_notification_message(self):
        notif_json = JSONRenderer().render(data=NotificationSerializer(self.notification).data).decode('utf-8')
        expected_json = f'{{"notification":{notif_json},"recipient_id":{self.notification.recipient_id},' \
                        f'"type":"send_notification"}}'

        received_json: str = NotificationsHandler.build_notification_message(self.notification)

        self.assertEqual(received_json, expected_json)

    @patch('notifications.handlers.NotificationSerializer')
    def test_build_notification_message_calls_notif_serializer(self, mock_notif_serializer):
        mock_notif_serializer.return_value = MagicMock(data='hello')
        NotificationsHandler.build_notification_message(self.notification)

        mock_notif_serializer.assert_called_once_with(self.notification)

    @patch('notifications.handlers.MessageRouter')
    @patch('notifications.handlers.NotificationsHandler.build_notification_message')
    @patch('notifications.handlers.NotificationsHandler.fetch_notification')
    @patch('notifications.handlers.asyncio.ensure_future')
    def test_receive_message_calls_expected_methods(self, mock_ensure, mock_fetch, mock_build_notif, mock_router):
        router_ret_mock = MagicMock()
        router_ret_mock.return_value = 'juice crew'
        mock_fetch.return_value = 'HipHop'
        mock_build_notif.return_value = 'Instrumental'
        mock_router.return_value = router_ret_mock

        is_processed = NotificationsHandler.receive_message('1')

        self.assertTrue(is_processed)

        mock_fetch.assert_called_once_with(1)
        mock_build_notif.assert_called_once_with(mock_fetch.return_value)
        mock_router.assert_called_once_with(mock_build_notif.return_value)
        mock_ensure.assert_called_once_with(router_ret_mock.return_value)

    @patch('notifications.handlers.NotificationsHandler.fetch_notification')
    def test_receive_message_returns_true_on_notif_already_read_error(self, mock_fetch):
        mock_fetch.side_effect = NotificationAlreadyRead()

        is_processed = NotificationsHandler.receive_message('1111')

        self.assertTrue(is_processed)
        mock_fetch.assert_called_once_with(1111)

    @patch('notifications.handlers.NotificationsHandler.fetch_notification')
    def test_receive_message_returns_true_on_notif_doesnt_exist_err(self, mock_fetch):
        mock_fetch.side_effect = Notification.DoesNotExist()
        is_processed = NotificationsHandler.receive_message('1111')

        self.assertTrue(is_processed)
        mock_fetch.assert_called_once_with(1111)

    @patch('notifications.handlers.NotificationsHandler.fetch_notification')
    def test_receive_message_returns_true_on_offlineRecipientError(self, mock_fetch):
        mock_fetch.side_effect = OfflineRecipientError()
        is_processed = NotificationsHandler.receive_message('1111')

        self.assertTrue(is_processed)
        mock_fetch.assert_called_once_with(1111)

    def test_receive_message_returns_false_on_invalid_message(self):
        """ This is unexpected, as most probably the message structure is not as expected
        (not a valid int for the parsing), as such, it should not bep rocessed """
        is_processed = NotificationsHandler.receive_message('{"notif_id": "1"}')
        self.assertFalse(is_processed)

    @patch('notifications.handlers.NotificationsHandler.fetch_notification')
    def test_receive_message_returns_false_on_other_error(self, mock_fetch):
        """ This is an unexpected error and as such the message should be marked as non-processed"""
        mock_fetch.side_effect = Exception()
        is_processed = NotificationsHandler.receive_message('1111')

        self.assertFalse(is_processed)
