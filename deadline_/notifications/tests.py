from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.renderers import JSONRenderer

from challenges.tests.base import TestHelperMixin
from notifications.errors import NotificationAlreadyRead
from notifications.handlers import NotificationsHandler
from social.models import Notification
from social.serializers import NotificationSerializer


class NotificationsHandlerTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.base_set_up(create_user=True)
        self.notification = Notification.objects.create_new_challenge_notification(recipient=self.auth_user, challenge=self.challenge)

    def test_fetch_notification_returns_notif(self):
        received_notif = NotificationsHandler.fetch_notification(self.notification.id)
        self.assertEqual(received_notif, self.notification)

    def test_fetch_notifications_raises_does_not_exist_if_id_invalid(self):
        with self.assertRaises(Notification.DoesNotExist):
            NotificationsHandler.fetch_notification(1123)

    def test_fetch_notifications_raises_notfication_already_read_if_notif_read(self):
        self.notification.is_read = True
        self.notification.save()

        with self.assertRaises(NotificationAlreadyRead):
            NotificationsHandler.fetch_notification(self.notification.id)

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
