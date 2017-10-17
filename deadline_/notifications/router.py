import asyncio
import json
import logging

from notifications.errors import MaliciousUserException
from .channels import user_authentication, read_notification

logger = logging.getLogger('notifications')


class MessageRouter:
    """
    The purpose of this class is to
        receive messages,
        parse the JSON string into a python dict
        send the message to the appropriate queue (which is connected to a handler)
    """
    MESSAGE_QUEUES = {
        'authentication': user_authentication,
        'read_notification': read_notification
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
            logger.error(f'Exception in MessageRouter while parsing JSON string - {e}')

    @asyncio.coroutine
    def __call__(self):
        logger.debug('routing message: {}'.format(self.packet))
        send_queue = self.get_send_queue()
        yield from send_queue.put(self.packet)

    def get_send_queue(self):
        return self.MESSAGE_QUEUES[self.packet['type']]
