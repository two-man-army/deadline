import asyncio
import json
import logging

from private_chat.errors import MaliciousUserException
from .channels import new_messages, is_typing, fetch_dialog_token

logger = logging.getLogger('django-private-dialog')


class MessageRouter:
    MESSAGE_QUEUES = {
        'new-message': new_messages,
        'fetch-token': fetch_dialog_token,
        'is-typing': is_typing,
    }

    def __init__(self, data, user_id):
        try:
            self.packet = json.loads(data)

            if 'user_id' in self.packet and self.packet['user_id'] != user_id:
                raise MaliciousUserException(f'User with ID {user_id} tried to mask himself as {self.packet["user_id"]}')

            self.packet['user_id'] = user_id
        except MaliciousUserException as e:
            logger.warn(str(e))
        except Exception as e:
            logger.debug(f'Could not load json: {e}')

    @asyncio.coroutine
    def __call__(self):
        logger.debug('routing message: {}'.format(self.packet))
        send_queue = self.get_send_queue()
        yield from send_queue.put(self.packet)

    def get_send_queue(self):
        return self.MESSAGE_QUEUES[self.packet['type']]
