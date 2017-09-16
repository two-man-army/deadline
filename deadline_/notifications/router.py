import asyncio
import json

class MessageRouter(object):
    """
    The purpose of this class is to
        receive messages,
        parse the JSON string into a python dict
        send the message to the appropriate queue (which is connected to a handler)
    """
    MESSAGE_QUEUES = {
    }

    def __init__(self, data):
        try:
            self.packet = json.loads(data)
        except Exception as e:
            pass

    @asyncio.coroutine
    def __call__(self):
        # logger.debug('routing message: {}'.format(self.packet))
        send_queue = self.get_send_queue()
        yield from send_queue.put(self.packet)

    def get_send_queue(self):
        return self.MESSAGE_QUEUES[self.packet['type']]
