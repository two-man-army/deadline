import json

from websockets import WebSocketServerProtocol


class WebSocketConnection:
    def __init__(self, socket: WebSocketServerProtocol, user_id):
        self.web_socket = socket
        self.user_id = user_id
        self.is_valid = False

    def __hash__(self):
        return hash(str(self.user_id))

    def __eq__(self, other):
        return self.user_id == other.user_id


class UserConnection(WebSocketConnection):
    """
    This class represents a connection to a User.
    It is responsible for keeping the state of the connection (authenticated or not)
        and for sending/receiving messages from it
    """
    def __init__(self, socket: WebSocketServerProtocol, user):
        super().__init__(socket, user.id)
        self.user = user

    async def receive_message(self):
        received_message = await self.web_socket.recv()
        print(f'Received message {received_message} from user {self.user_id}')
        return received_message

    async def send_message(self, payload):
        """
        Sends a payload (message) to one connection
        """
        try:
            await self.web_socket.send(json.dumps(payload))
        except Exception as e:
            print(f'Could not send message to websocket due to {e}')

