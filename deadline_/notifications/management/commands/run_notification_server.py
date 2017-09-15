import asyncio

import uvloop
import websockets

from django.conf import settings
from django.core.management.base import BaseCommand
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())  # needs to be set before websockets for some reason
from notifications import channels, handlers


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

        # asyncio.async(handlers.new_messages_handler(channels.new_messages))
        # asyncio.async(handlers.fetch_dialog_token(channels.fetch_dialog_token))
        # asyncio.async(handlers.is_typing_handler(channels.is_typing))
        loop = asyncio.get_event_loop()
        loop.run_forever()
