import asyncio
import json
import logging

from .channels import new_messages, users_changed, online, offline, check_online, is_typing, fetch_dialog_token

logger = logging.getLogger('django-private-dialog')


class MessageRouter(object):
    MESSAGE_QUEUES = {
        'new-message': new_messages,
        'fetch-token': fetch_dialog_token,
        # 'new-user': users_changed,
        # 'online': online,
        # 'offline': offline,
        # 'check-online': check_online,
        # 'is-typing': is_typing,
    }

    def __init__(self, data):
        try:
            self.packet = json.loads(data)
        except Exception as e:
            logger.debug('could not load json: {}'.format(str(e)))

    @asyncio.coroutine
    def __call__(self):
        logger.debug('routing message: {}'.format(self.packet))
        print('routing message')
        send_queue = self.get_send_queue()
        yield from send_queue.put(self.packet)

    def get_send_queue(self):
        return self.MESSAGE_QUEUES[self.packet['type']]
