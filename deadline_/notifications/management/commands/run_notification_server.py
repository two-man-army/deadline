import asyncio

import uvloop
import websockets

from django.conf import settings
from django.core.management.base import BaseCommand

from notifications.notifications_consumer import NotificationConsumer

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # needs to be set before websockets for some reason
from notifications import channels, handlers
from deadline.settings import RABBITMQ_CONNECTION_URL


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
        loop = asyncio.get_event_loop()

        NotificationConsumer(RABBITMQ_CONNECTION_URL).run()

        print(f'Running WS server on {settings.NOTIFICATIONS_WS_SERVER_HOST}:{settings.NOTIFICATIONS_WS_SERVER_PORT}')
        loop.run_forever()
