import websockets

from accounts.models import User
from notifications.classes import UserConnection
from notifications.helpers import extract_connect_path
from notifications.router import MessageRouter

ws_connections: {int: UserConnection} = {}


async def authenticate_user(stream):
    while True:
        auth_message = await stream.get()
        print(auth_message)

async def main_handler(websocket, path):
    user_id = extract_connect_path(path)
    try:
        # TODO: validate user_id
        # owner, opponent = fetch_and_validate_participants(owner_id, opponent_id)
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
