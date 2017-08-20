import asyncio
import json
import logging
import websockets

from django.contrib.auth import get_user_model

from accounts.models import User
from private_chat.errors import ChatPairingError, UserTokenMatchError
from private_chat.helpers import extract_connect_path
from private_chat.models import Dialog
from private_chat.services.dialog import get_or_create_dialog_token
from . import models, router
from django.contrib.sessions.models import Session


class WebSocketConnection:
    def __init__(self, socket, owner_id, opponent_id):
        self.web_socket = socket
        self.owner_id = owner_id
        self.opponent_id = opponent_id
        self.is_valid = False

    def validate(self):
        self.is_valid = True

    def invalidate(self):
        self.is_valid = False

    def __hash__(self):
        return hash(str(self.owner_id) + str(self.opponent_id))

    def __eq__(self, other):
        return self.owner_id == other.owner_id and self.opponent_id == other.opponent_id


def get_user_from_session(session_key):
    """
    Gets the user from current User model using the passed session_key
    :param session_key: django.contrib.sessions.models.Session - session_key
    :return: User instance or None if not found
    """
    session = Session.objects.get(session_key=session_key)
    session_data = session.get_decoded()
    uid = session_data.get('_auth_user_id')
    user = get_user_model().objects.filter(id=uid).first()  # get object or none
    return user


logger = logging.getLogger('django-private-dialog')
ws_connections: {(int, int): WebSocketConnection} = {}


@asyncio.coroutine
def send_message(conn, payload):
    """
    Distibuted payload (message) to one connection
    """
    try:
        yield from conn.send(json.dumps(payload))
    except Exception as e:
        logger.debug(f'Could not send message to websocket due to {e}')


@asyncio.coroutine
def fanout_message(connections, payload):
    """
    distributes payload (message) to all connected ws clients
    """
    for conn in connections:
        try:
            yield from conn.send(json.dumps(payload))
        except Exception as e:
            logger.debug(f'Could not send message to multiple websockets due to {e}')


@asyncio.coroutine
def gone_online(stream):
    """
    Distributes the users online status to everyone he has dialog with
    """
    while True:
        packet = yield from stream.get()
        session_id = packet.get('session_key')
        if session_id:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                logger.debug('User '+user_owner.username+' gone online')
                # find all connections including user_owner as opponent,
                # send them a message that the user has gone online
                online_opponents = list(filter(lambda x: x[1] == user_owner.username, ws_connections))
                online_opponents_sockets = [ws_connections[i] for i in online_opponents]
                yield from fanout_message(online_opponents_sockets,
                                          {'type': 'gone-online', 'usernames': [user_owner.username]})
            else:
                pass  # invalid session id
        else:
            pass  # no session id


@asyncio.coroutine
def check_online(stream):
    """
    Used to check user's online opponents and show their online/offline status on page on init
    """
    while True:
        packet = yield from stream.get()
        session_id = packet.get('session_key')
        opponent_username = packet.get('username')
        if session_id and opponent_username:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                # Find all connections including user_owner as opponent
                online_opponents = list(filter(lambda x: x[1] == user_owner.username, ws_connections))
                logger.debug('User '+user_owner.username+' has '+str(len(online_opponents))+' opponents online')
                # Send user online statuses of his opponents
                socket = ws_connections.get((user_owner.username, opponent_username))
                if socket:
                    online_opponents_usernames = [i[0] for i in online_opponents]
                    yield from send_message(socket,
                                              {'type': 'gone-online', 'usernames': online_opponents_usernames})
                else:
                    pass  # socket for the pair user_owner.username, opponent_username not found
                    # this can be in case the user has already gone offline
            else:
                pass  # invalid session id
        else:
            pass  # no session id or opponent username


@asyncio.coroutine
def gone_offline(stream):
    """
    Distributes the users online status to everyone he has dialog with
    """
    while True:
        packet = yield from stream.get()
        session_id = packet.get('session_key')
        if session_id:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                logger.debug('User '+user_owner.username+' gone offline')
                # find all connections including user_owner as opponent,
                #  send them a message that the user has gone offline
                online_opponents = list(filter(lambda x: x[1] == user_owner.username, ws_connections))
                online_opponents_sockets = [ws_connections[i] for i in online_opponents]
                yield from fanout_message(online_opponents_sockets,
                                          {'type': 'gone-offline', 'username': user_owner.username})
            else:
                pass  # invalid session id
        else:
            pass  # no session id


@asyncio.coroutine
def fetch_dialog_token(stream):
    """
    Returns the Dialog token for a specific conversation and for the specific participant

    Needs to be sent the following JSON
    {
    "type": "fetch-token",
    "user_id": YOUR_USER_ID_HERE,
    "auth_token": YOUR_AUTH_TOKEN_HERE,
    "opponent_id": HIS_ID_HERE
    }
    """
    while True:
        packet = yield from stream.get()
        owner_id, opponent_id = int(packet.get('user_id', '-1')), int(packet.get('opponent_id', '-1'))

        to_send_message, payload = _fetch_dialog_token(packet, owner_id, opponent_id)
        if to_send_message:
            yield from send_message(ws_connections[(owner_id, opponent_id)].web_socket, payload)

            opponent_is_online = (opponent_id, owner_id) in ws_connections and ws_connections[(opponent_id, owner_id)].is_valid
            yield from send_message(ws_connections[(owner_id, opponent_id)].web_socket,
                                    {'type': 'online-check', 'is_online': opponent_is_online})
            # Notify the opponent that we came online
            if opponent_is_online:
                yield from send_message(ws_connections[(opponent_id, owner_id)].web_socket,
                                        {'type': 'online-check', 'is_online': True})


def _fetch_dialog_token(packet: dict, owner_id, opponent_id) -> (bool, dict):
    """
    :return:
        - boolean indicating if we want to send a message
        - the payload we would send
    """
    if (owner_id, opponent_id) not in ws_connections:
        return False, {}  # we do not have such a connection. Either malicious or a mistake, but we cant respond back

    try:
        owner, opponent = fetch_and_validate_participants(owner_id, opponent_id)
        if owner.auth_token.key != packet.get('auth_token'):  # authenticate user
            raise UserTokenMatchError(f'Invalid token!')
    except (User.DoesNotExist, UserTokenMatchError) as e:
        logger.debug(f'Raised {e.__class__} in fetch-token handler. Error message was {str(e)}')

        return True, {'error': str(e)}

    token = get_or_create_dialog_token(owner, opponent)
    ws_connections[(owner_id, opponent_id)].is_valid = True
    return True, {'conversation_token': token}


@asyncio.coroutine
def new_messages_handler(stream):
    """
    Receives a message from a user and direct it to the recipient

    Needs to be sent the following JSON
    {
        "type": "new-message",
        "message": "YOUR_MESSAGE_HERE",
        "user_id": YOUR_USER_ID_HERE,
        "opponent_id": HIS_ID_HERE,
        "conversation_token": YOUR_CONVESRATION_TOKEN_HERE
    }
    """
    while True:
        packet = yield from stream.get()
        owner_id, opponent_id = packet.get('user_id'), packet.get('opponent_id')
        to_send, is_err, payload = _new_messages_handler(packet, owner_id, opponent_id)

        if to_send:
            owner_id, opponent_id = int(owner_id), int(opponent_id)
            owner_socket = ws_connections[(owner_id, opponent_id)]

            connections = [owner_socket.web_socket]
            if not is_err and (opponent_id, owner_id) in ws_connections:
                opponent_socket: WebSocketConnection = ws_connections[(opponent_id, owner_id)]
                if opponent_socket.is_valid:
                    connections.append(opponent_socket.web_socket)

            yield from fanout_message(connections, payload)


def _new_messages_handler(packet: dict, owner_id, opponent_id):
    """
    Validates the user_ids, the connection's validity and owner's authorization and sends the message to both
    """
    if (owner_id, opponent_id) not in ws_connections:
        return False, True, {}  # no such connection, we cannot send this to anybody

    message = packet.get('message')
    if not message:
        return True, True, {'error': 'Message cannot be empty!'}

    try:
        owner, opponent = fetch_and_validate_participants(owner_id, opponent_id)
    except (User.DoesNotExist, ChatPairingError) as e:
        return True, True, {'error': str(e)}  # should not happen, as we should not have a non-existent user in ws_connections

    owner_socket: WebSocketConnection = ws_connections[(owner.id, opponent.id)]
    if not owner_socket.is_valid:
        return True, True, {'error': 'You need to authorize yourself by fetching a token!'}

    conversation_token = packet.get('conversation_token')

    dialog: Dialog = Dialog.objects.get_or_create_dialog_with_users(owner, opponent)
    if not dialog.token_is_valid(conversation_token):
        return True, True, {'error': 'Invalid conversation_token. Fetch a new one!'}

    msg = models.Message.objects.create(
        dialog=dialog,
        sender=owner,
        text=message
    )

    payload_to_send = {
        'type': 'received-message',
        'created': msg.get_formatted_create_datetime(),
        'sender_name': msg.sender.username,
        'message': message,
        'id': msg.id
    }

    return True, False, payload_to_send

# @asyncio.coroutine
# def users_changed_handler(stream):
#     """
#     Sends connected client list of currently active users in the chatroom
#     """
#     while True:
#         yield from stream.get()
#
#         # Get list list of current active users
#         users = [
#             {'username': username, 'uuid': uuid_str}
#             for username, uuid_str in ws_connections.values()
#         ]
#
#         # Make packet with list of new users (sorted by username)
#         packet = {
#             'type': 'users-changed',
#             'value': sorted(users, key=lambda i: i['username'])
#         }
#         logger.debug(packet)
#         yield from fanout_message(ws_connections.keys(), packet)

#
# @asyncio.coroutine
# def is_typing_handler(stream):
#     """
#     Show message to opponent if user is typing message
#     """
#     while True:
#         packet = yield from stream.get()
#         session_id = packet.get('session_key')
#         user_opponent = packet.get('username')
#         typing = packet.get('typing')
#         if session_id and user_opponent and typing is not None:
#             user_owner = get_user_from_session(session_id)
#             if user_owner:
#                 opponent_socket = ws_connections.get((user_opponent, user_owner.username))
#                 if typing and opponent_socket:
#                     yield from target_message(opponent_socket,
#                                               {'type': 'opponent-typing', 'username': user_opponent})
#             else:
#                 pass  # invalid session id
#         else:
#             pass  # no session id or user_opponent or typing


@asyncio.coroutine
def main_handler(websocket, path):
    """
    An Asyncio Task is created for every new websocket client connection
    that is established. This coroutine listens to messages from the connected
    client and routes the message to the proper queue.

    This coroutine can be thought of as a producer.

    Expected path for initial connection is
    /user_id/user_token/user_to_speak_to_id
    """
    owner_id, opponent_id = extract_connect_path(path)
    try:
        owner, opponent = fetch_and_validate_participants(owner_id, opponent_id)
    except (ChatPairingError, User.DoesNotExist) as e:
        print(str(e))
        return

    if (owner.id, opponent.id) not in ws_connections:
        ws_connections[(owner.id, opponent.id)] = WebSocketConnection(websocket, owner_id, opponent_id)

    yield from send_message(websocket, {'tank': 'YOU ARE CONNECTED :)'})

    # While the websocket is open, listen for incoming messages/events
    try:
        while websocket.open:
            data = yield from websocket.recv()
            if not data:
                continue

            try:
                logger.debug(f'Data is {data}')
                yield from router.MessageRouter(data)()
            except Exception as e:
                logger.error(f'Could not route message {e}')

    except websockets.exceptions.InvalidState:  # User disconnected
        pass
    finally:
        del ws_connections[(owner.id, opponent.id)]
        if (opponent.id, owner.id) in ws_connections and ws_connections[(opponent.id, owner.id)].is_valid:
            yield from send_message(ws_connections[(opponent.id, owner.id)].web_socket,
                                    {'type': 'online-check', 'is_online': False})


def fetch_and_validate_participants(owner_id: int, opponent_id: int) -> (User, User):
    """
    Fetches the User objects and validates them
    """
    if owner_id == opponent_id:
        raise ChatPairingError('Cannot match a user to himself!')
    owner = User.objects.get(id=owner_id)
    opponent = User.objects.get(id=opponent_id)

    return owner, opponent
