import pika


class RabbitMQClient:
    def __init__(self, connection_params):
        self.connection = pika.BlockingConnection(connection_params)
        self.channel = self.connection.channel()
        self.init_notification_exchange()

    def init_notification_exchange(self):
        self.channel.exchange_declare(exchange='notifications', exchange_type='fanout')

    def send_notification_message(self, notif_id: int):
        """
        Sends a message that a notification has been created
        """
        self.channel.basic_publish(exchange='notifications', routing_key='', body=str(notif_id))
