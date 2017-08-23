import re
from datetime import datetime, timedelta
from uuid import uuid4

import jwt

from accounts.models import User
from private_chat.constants import CONNECT_PATH_REGEX, DIALOG_TOKEN_EXPIRY_MINUTES
from private_chat.errors import RegexMatchError, ChatPairingError


def extract_connect_path(path):
    """
    Sample path: /chat/user_id/user_to_speak_to_id
    """
    match_obj = re.match(CONNECT_PATH_REGEX, path)
    if match_obj is None:
        raise RegexMatchError(f'Path {path} does not match the expected regex!')
    regex_groups = match_obj.groupdict()
    owner_id = int(regex_groups['owner_id'])
    opponent_id = int(regex_groups['opponent_id'])

    return owner_id, opponent_id


def generate_dialog_tokens(owner_name: str, opponent_name: str):
    """
    Generates a new secret_key and tokens for each participant
    """
    secret_key = uuid4().hex
    expiry_date = get_utc_time() + timedelta(minutes=DIALOG_TOKEN_EXPIRY_MINUTES)
    owner_token = jwt.encode({'exp': expiry_date, 'username': owner_name}, secret_key).decode("utf-8")
    opponent_token = jwt.encode({'exp': expiry_date, 'username': opponent_name}, secret_key).decode("utf-8")

    return secret_key, owner_token, opponent_token


def fetch_and_validate_participants(owner_id: int, opponent_id: int) -> (User, User):
    """
    Fetches the User objects and validates them
    """
    if owner_id == opponent_id:
        raise ChatPairingError('Cannot match a user to himself!')
    owner = User.objects.get(id=owner_id)
    opponent = User.objects.get(id=opponent_id)

    return owner, opponent


def get_utc_time():
    return datetime.utcnow()
