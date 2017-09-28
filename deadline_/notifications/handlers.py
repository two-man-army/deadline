import asyncio
import websockets
import logging

from accounts.models import User
from notifications.classes import UserConnection
from notifications.errors import NotificationAlreadyRead, OfflineRecipientError, InvalidNotificationToken, \
    RecipientMismatchError
from notifications.helpers import extract_connect_path
from notifications.router import MessageRouter
from social.models import Notification
from social.serializers import NotificationSerializer

"""
REVISIT: This way of handling connections is not scalable in the slightest way - 
    we can never run more than one process of this server, as the ws_connections variable will not get shared
IDEA:    Maybe it could get shared via some message broker (e.g connection established/authenticated/disconnected) 
            or store it in something like Redis or a DB?
IDEA:    Maybe we could rewrite it to something which allows parallelism with shared memory
"""
logger = logging.getLogger('notifications')
ws_connections: {int: UserConnection} = {}


class NotificationsHandler:
    """
    This class receives a Notification message from RabbitMQ through the `receive_message()` method
        and sends it out to the recipient if he is connected
    It expects the message to be a simple ID(integer), e.g "1"
    """

    @staticmethod
    def fetch_notification(notif_id: int) -> Notification:
        """
        Fetches a notification and validates it
        """
        notif: Notification = Notification.objects.get(id=notif_id)
        try:
            NotificationsHandler.validate_notification(notif)
        except (NotificationAlreadyRead, OfflineRecipientError) as e:
            raise e

        return notif

    @staticmethod
    def validate_notification(notif: Notification):
        """
        Validates that the notification is not read, that the recipient is connected and validated
        """
        if notif.is_read:
            raise NotificationAlreadyRead(f'Notification with ID {notif.id} is already read!')
        elif notif.recipient_id not in ws_connections:
            raise OfflineRecipientError(f'The notification recipient {notif.recipient_id} is not connected!')
        elif not ws_connections[notif.recipient_id].is_valid:
            raise OfflineRecipientError(f'The notification recipient {notif.recipient_id} is not authorized!')

    @staticmethod
    def receive_message(msg: str) -> bool:
        """
        Processes the message and sends it to the handler
        :return: a boolean indicating if hte message was successfully processed
        """
        try:
            notif_id = int(msg)
            notification = NotificationsHandler.fetch_notification(notif_id)

            asyncio.ensure_future(NotificationsHandler.send_notification(notification))
        except (NotificationAlreadyRead, Notification.DoesNotExist) as e:
            print(f'DEBUG - Notification was either read or with an invalid ID - {e}')
        except OfflineRecipientError as e:
            print(f'Recipient was not eligible to receive the message - {e}')
        except ValueError as e:
            print(f'Value error, most probably while parsing MSG - msg: {msg}\n {e}')
            return False
        except Exception as e:
            print(f'Exception while receiving a message - {e}')
            return False

        return True

    @staticmethod
    async def send_notification(notification: Notification):
        """
        Sends the following JSON to the recipient
        {
            "type": "NOTIFICATION",
            "notification": {...}
        }
        """
        recipient_id = notification.recipient_id
        if recipient_id not in ws_connections or not ws_connections[recipient_id].is_valid:
            print(f'Notification recipient with ID {recipient_id} was either not connected or not authorized')
            return

        asyncio.ensure_future(ws_connections[recipient_id].send_message({
            "type": "NOTIFICATION",
            "notification": NotificationSerializer(notification).data
        }))


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
            "type": "INVALID_NOTIFICATION_TOKEN",
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

        user_connection: UserConnection = ws_connections[user_id]
        if not user_connection.user.notification_token_is_valid(token):
            # TODO: This means that User 2 can spam an invalid token posing as User 3 and User 3 will receive a series of ERROR messages
            asyncio.ensure_future(user_connection.send_message({
                "type": "INVALID_NOTIFICATION_TOKEN",
                "message": "Notification token is invalid or expired!"
            }))
            continue

        # User has authenticated
        user_connection.is_valid = True
        asyncio.ensure_future(user_connection.send_message({
            "type": "OK",
            "message": "Successfully authenticated!"
        }))


def _read_notification(notification_token, user_id, notification_id):
    if user_id not in ws_connections:
        print(f'Somebody else tried to authenticate user_id {user_id}.')
        raise OfflineRecipientError(f'Somebody else tried to authenticate user_id {user_id}.')
    if not ws_connections[user_id].is_valid:
        raise OfflineRecipientError(f'User {user_id} is not authenticated!')

    user_connection: UserConnection = ws_connections[user_id]
    if not user_connection.user.notification_token_is_valid(notification_token):
        # TODO: This means that User 2 can spam an invalid token posing as User 3 and User 3 will receive a series of ERROR messages
        raise InvalidNotificationToken(f'User with ID {user_id} provided an invalid notification token {notification_token}!')

    notif = Notification.objects.get(id=notification_id)
    if not notif.is_recipient(user_connection.user):
        raise RecipientMismatchError(f'User {user_id} is not the recipient for notification {notification_id}')

    notif.is_read = True
    notif.save()

async def read_notification(stream):
    """
    Marks a notification as read by the user.

    Expects the following JSON
    {
        "type": "read_notification",
        "notification_id": {Notification ID}
        "user_id": {User ID}
        "token": {User Notification Token}
    }
    Can either send a
        {
            "type": "ERROR"
            "message": "XXX"
        }
        or a
        {
            "type": "OK",
            "message": ""
        }
    """

    while True:
        message = await stream.get()

        token, user_id, notif_id = message.get('token'), message.get('user_id'), message.get('notification_id')

        try:
            _read_notification(token, user_id, notif_id)
            asyncio.ensure_future(ws_connections[user_id].send_message({
                "type": "OK",
                "message": f"Notification with ID {notif_id} was read successfully"
            }))
        except InvalidNotificationToken:
            asyncio.ensure_future(ws_connections[user_id].send_message({
                "type": "INVALID_NOTIFICATION_TOKEN",
                "message": "Notification token is invalid or expired!"
            }))
        except (RecipientMismatchError, Notification.DoesNotExist):
            asyncio.ensure_future(ws_connections[user_id].send_message({
                "type": "ERROR",
                "message": "You are not the recipient of that notification!"
            }))
        except OfflineRecipientError:
            pass


async def main_handler(websocket, path):
    user_id = extract_connect_path(path)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as e:
        print(str(e))
        return

    if user.id in ws_connections:
        # This websocket is already connected, overwrite it only if it is not authenticated
        if ws_connections[user.id].is_valid:
            logger.debug(f'Tried to overwrite socket with ID {user.id} but did not since it was valid!')
            return
        logger.debug(f'Overwrote socket with ID {user.id}')

    ws_connections[user.id] = UserConnection(websocket, user)

    asyncio.ensure_future(ws_connections[user_id].send_message({
        "type": "OK",
        "message": "Connected!"
    }))

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
                await MessageRouter(data)()
            except Exception as e:
                logger.error(f'Could not route message {e}')

    except websockets.exceptions.InvalidState:  # User disconnected
        logger.debug(f'User {user_id} most likely disconnected!')
    finally:
        if not is_overwritten:
            del ws_connections[user.id]
        else:
            logger.debug(f'Deleted old overwritten socket with ID {user_id}')
