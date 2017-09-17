import asyncio
import websockets

from accounts.models import User
from notifications.classes import UserConnection
from notifications.helpers import extract_connect_path
from notifications.router import MessageRouter

ws_connections: {int: UserConnection} = {}


class NotificationsHandler:
    """
    This class receives a Notification message from RabbitMQ and sends it out to the appropriate
    """

    @staticmethod
    def receive_message(msg: str) -> bool:
        try:
            print(f'Notifications handler received msg {msg}')
            # TODO: Parse notif id, fetch notif, check if read
            print('Sending message to async router')
            # asyncio.ensure_future(MessageRouter('{"type": "authentication"}')())
            pass
        except Exception:
            return False

        return True

    @staticmethod
    async def send_notification(stream):
        """
        Expects a Notification JSON in the following form:
        {
            "notification": {notification_object},
            "recipient_id": {ID of the user who is meant to receive this}
        }

        Sends the following JSON to the recipient
        {
            "type": "NOTIFICATION",
            "notification": {...}
        }
        """
        while True:
            notification_obj = await stream.get()


async def authenticate_user(stream):
    """
    Authenticates the user, essentially validating his connection
        and proving he is who he claims to be
    Expects the following JSON
    {
    "type": "authentication",
    "token": YOUR_NOTIFICATION_TOKEN_HERE,
    "user_id": YOUR_ID_HERE,
    }
    Can either return
        an error message
        {
            "type": "ERROR",
            "message": "Notification token is invalid or expired!"
        }
        an OK acknowledgement
        {
            "type": "OK",
            "message": "Successfully authenticated"
        }
    """
    while True:
        auth_message = await stream.get()
        token, user_id = auth_message.get('token'), auth_message.get('user_id')
        if user_id not in ws_connections:
            print(f'Somebody else tried to authenticate user_id {user_id}.')
            continue

        user: User = User.objects.get(id=user_id) # TODO: Maybe store user in his connection?
        user_connection: UserConnection = ws_connections[user.id]
        if not user.notification_token_is_valid(token):
            asyncio.ensure_future(user_connection.send_message({
                "type": "ERROR",
                "message": "Notification token is invalid or expired!"
            }))
            continue

        # User has authenticated
        user_connection.is_valid = True
        asyncio.ensure_future(user_connection.send_message({
            "type": "OK",
            "message": "Successfully authenticated!"
        }))


async def main_handler(websocket, path):
    user_id = extract_connect_path(path)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as e:
        print(str(e))
        return

    if user.id in ws_connections:
        # This websocket is already connected, overwrite it only if it is not authenticate
        if ws_connections[user.id].is_valid:
            # logger.debug(f'Tried to overwrite socket with ID {(owner.id, opponent.id)} but did not since it was valid!')
            return
        # logger.debug(f'Overwrote socket with ID {(owner.id, opponent.id)}')

    ws_connections[user.id] = UserConnection(websocket, user.id)

    # TODO: Send confirmation message
    # await send_message(websocket, {'tank': 'YOU ARE CONNECTED :)'})

    # While the websocket is open, listen for incoming messages/events
    is_overwritten = False
    try:
        while websocket.open:
            data = await ws_connections[user.id].receive_message()
            if ws_connections[user.id].web_socket != websocket:
                # This socket has been overwritten, so stop it
                is_overwritten = True
                return

            if not data:
                continue

            try:
                print(f'Data is {data}')
                # TODO: Define authentication message handler and notification read handler
                await MessageRouter(data)()
            except Exception as e:
                pass
                # logger.error(f'Could not route message {e}')

    except websockets.exceptions.InvalidState:  # User disconnected
        pass
    finally:
        if not is_overwritten:
            del ws_connections[user.id]
        else:
            pass
            # logger.debug(f'Deleted old overwritten socket with ID {(owner.id, opponent.id)}')
