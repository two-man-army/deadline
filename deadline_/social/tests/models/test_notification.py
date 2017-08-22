from unittest.mock import patch

from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from social.errors import InvalidNotificationType, MissingNotificationContentField, InvalidNotificationContentField
from social.models import Notification


class NotifiationItemTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()

    def test_model_save_raises_if_invalid_notification_type(self):
        """ An error should be raised if we enter an invalid newsfeeditem type """
        with self.assertRaises(InvalidNotificationType):
            Notification.objects.create(recipient=self.auth_user, type='TANK',
                                        content={'content': 'Hello I like turtles'})

    @patch('social.models.VALID_NOTIFICATION_TYPES', ['test_type'])
    @patch('social.models.NOTIFICATION_TYPE_CONTENT_FIELDS', {'test_type': ['1', '2']})
    def test_model_save_raises_if_missing_newsfeed_content_field(self):
        """ Given a valid Newsfeed Type, an error should be raised if a required field is missing """
        with self.assertRaises(MissingNotificationContentField):
            Notification.objects.create(recipient=self.auth_user, type='test_type',
                                        content={})

    @patch('social.models.VALID_NOTIFICATION_TYPES', ['test_type'])
    @patch('social.models.NOTIFICATION_TYPE_CONTENT_FIELDS', {'test_type': ['1', '2']})
    def test_model_save_raises_if_invalid_newsfeed_content_field(self):
        """ Given a valid Newsfeed Type, an error should be raised if an invalid field is added,
                regardless if all the right ones are supplied (memory is expensive) """
        with self.assertRaises(InvalidNotificationContentField):
            Notification.objects.create(recipient=self.auth_user, type='test_type',
                                        content={'1': 'Hello I like turtles', '2': 'pf', 'tank': 'yo'})
