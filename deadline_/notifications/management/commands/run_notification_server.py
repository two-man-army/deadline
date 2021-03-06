import asyncio

import logging
import uvloop
import websockets

from django.conf import settings
from django.core.management.base import BaseCommand

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # needs to be set before websockets for some reason

from notifications import channels, handlers
from notifications.notifications_consumer import NotificationsConsumerConnection
from deadline.settings import RABBITMQ_CONNECTION_URL

logger = logging.getLogger('notifications')


class Command(BaseCommand):
    help = 'Starts message center chat engine'

    def handle(self, *args, **options):
        asyncio.async(
            websockets.serve(
                handlers.main_handler,
                settings.NOTIFICATIONS_WS_SERVER_HOST,
                settings.NOTIFICATIONS_WS_SERVER_PORT
            )
        )

        asyncio.async(handlers.authenticate_user(channels.user_authentication))
        asyncio.async(handlers.read_notification(channels.read_notification))
        loop = asyncio.get_event_loop()

        NotificationsConsumerConnection(RABBITMQ_CONNECTION_URL, handlers.NotificationsHandler).run()
        logger.info(f'Running WS server on {settings.NOTIFICATIONS_WS_SERVER_HOST}:{settings.NOTIFICATIONS_WS_SERVER_PORT}')
        loop.run_forever()
