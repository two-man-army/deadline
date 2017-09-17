"""
The RabbitMQ class which establishes the connection, creates exchanges/queues and delegates messages
"""
import pika
from pika import adapters
from pika.spec import BasicProperties, Basic
from pika.channel import Channel
from pika.frame import Method as FrameMethod


class BaseRabbitMQConsumerConnection:
    """
    This is the base class of a RabbitMQ consumer, it sets up and maintains the connection.
    Classes should inherit this and define the needed static variables t be able to properly set up a connection
    A handler object must also be sent, one who processes the message. see: on_message method

    The RabbitMQ connection which is part of the async event loop and receives notifications for it to send out

    If RabbitMQ closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    Quick summary of how this class works:

    NotificationConsumer('localhost:5002...").run() -> calls connect(),
        which triggers a chain of on_success_xxx methods. These methods declare the exchange, the queue, bind the queue
            and setup the correct handlers for receiving a message and closing a connection
    """
    NEEDED_STATIC_VARIABLES = ['EXCHANGE', 'EXCHANGE_TYPE', 'QUEUE', 'ROUTING_KEY']

    def __init__(self, amqp_url: str, handler):
        """
        :param str amqp_url: The AMQP url to connect with
        """
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self.handler = handler
        self._validate_instantiation()

    def run(self):
        """
        Run the example consumer by connecting to RabbitMQ
        """
        self._connection = self.connect()

    def connect(self) -> pika.adapters.AsyncioConnection:
        """
        When the connection is established, the on_connection_open method will be invoked by pika.
        This triggers a chains of on_success_xxx methods which declare an exchange, a queue and bind said queue
        """
        # LOGGER.info('Connecting to %s', self._url)
        return adapters.AsyncioConnection(pika.URLParameters(self._url),
                                          self.on_connection_open)

    def on_message(self, _: Channel, basic_deliver: Basic.Deliver,
                   __: BasicProperties, body: str):
        """
        The heart of this class, this is the method that processes a received message
        It sends it to the consumer's receive_message method and expects a boolean value returned, indicating
            if the message was processed
        """
        # LOGGER.info('Received message # %s from %s: %s',
        #             basic_deliver.delivery_tag, properties.app_id, body)
        print(f'Received message {body}')
        was_processed = self.handler.receive_message(body)

        if was_processed:
            self._channel.basic_ack(basic_deliver.delivery_tag)  # acknowledge that the message has been processed

    # Setup methods

    def on_connection_open(self, _: pika.adapters.AsyncioConnection):
        """
        This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.
        """
        # LOGGER.info('Connection opened')
        print('Conneced to rabbitmq')
        self._connection.add_on_close_callback(self.on_connection_closed)
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel: Channel):
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)

        self.setup_exchange(self.EXCHANGE)

    def setup_exchange(self, exchange_name: str):
        # LOGGER.info('Declaring exchange %s', exchange_name)
        print(f'Declaring exchange {exchange_name}')
        self._channel.exchange_declare(self.on_successful_exchange_declaration,
                                       exchange_name,
                                       self.EXCHANGE_TYPE)

    def on_successful_exchange_declaration(self, _: FrameMethod):
        # LOGGER.info('Exchange declared')
        self._channel.queue_declare(self.on_successful_queue_declaration, self.QUEUE)

    def on_successful_queue_declaration(self, _: FrameMethod):
        """
        Binds the queue to the exchange
        """
        # LOGGER.info('Binding %s to %s with %s',
        #             self.EXCHANGE, self.QUEUE, self.ROUTING_KEY)
        self._channel.queue_bind(self.on_bindok, self.QUEUE,
                                 self.EXCHANGE, self.ROUTING_KEY)

    def on_bindok(self, _: FrameMethod):
        """
        Invoked when a queue is successfully binded. Starts consumation of messages
        """
        # LOGGER.info('Queue bound')
        # Start consuming messages
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.QUEUE)

    # Close connection methods/handlers

    def close_connection(self):
            """This method closes the connection to RabbitMQ."""
            # LOGGER.info('Closing connection')
            self._connection.close()

    def on_connection_closed(self, _: adapters.AsyncioConnection, reply_code: int, reply_text: str):
        """
        This method is invoked by pika when the connection to RabbitMQ is closed unexpectedly.
        Since it is unexpected, we will reconnect to RabbitMQ if it disconnects.
        """
        self._channel = None
        if not self._closing:
            # LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
            #                reply_code, reply_text)
            # Attempt to reconnect
            self._connection.add_timeout(5, self.reconnect)

    def on_channel_closed(self, channel: Channel, reply_code: int, reply_text: str):
        """
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.
        This also gets called when we cleanly shutdown the connection from the code
        """
        # LOGGER.warning('Channel %i was closed: (%s) %s',
        #                channel, reply_code, reply_text)
        self._connection.close()

    def on_consumer_cancelled(self, _: FrameMethod):
        # LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
        #             method_frame)
        if self._channel:
            self._channel.close()

    def on_cancelok(self, _: FrameMethod):
        """
        This method is invoked by pika when RabbitMQ acknowledges the cancellation of a consumer.
        At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
            closed, which will in-turn close the connection.
        """
        # LOGGER.info('RabbitMQ acknowledged the cancellation of the consumer; Closing the channel')
        self._channel.close()

    def stop(self):
        """
        Cleanly shuts down the connection
        """
        # LOGGER.info('Stopping')
        print('Stopping RabbitMQ')
        self._closing = True
        if self._channel:
            # LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)
        print('Stopped RabbitMQ')
        # LOGGER.info('Stopped')

    def reconnect(self):
        """
        Will be invoked by the IOLoop timer if the connection is closed.
        """
        if not self._closing:
            self._connection = self.connect()

    def _validate_instantiation(self):
        """ Validates that the class was instantiated properly"""
        for var_name in self.NEEDED_STATIC_VARIABLES:
            if not hasattr(self, var_name):
                raise Exception(f'{var_name} needs to be defined for {self.__class__.__name__}')
        if not hasattr(self.handler, 'receive_message'):
            raise Exception('Consumer is required to have defined the receive_message method!')


class NotificationsConsumerConnection(BaseRabbitMQConsumerConnection):
    """
    This class defines the needed variables to establish a RabbitMQ connection
    """
    EXCHANGE = 'notifications'
    EXCHANGE_TYPE = 'fanout'
    QUEUE = 'text'
    ROUTING_KEY = 'example.text'
