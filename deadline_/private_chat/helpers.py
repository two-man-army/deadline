import re
from datetime import datetime, timedelta
from uuid import uuid4

import jwt

from private_chat.constants import CONNECT_PATH_REGEX, DIALOG_TOKEN_EXPIRY_MINUTES
from private_chat.errors import RegexMatchError


def extract_connect_path(path):
    """
    Sample path: /user_id/user_token/user_to_speak_to_id
    """
    match_obj = re.match(CONNECT_PATH_REGEX, path)
    if match_obj is None:
        raise RegexMatchError(f'Path {path} does not match the expected regex!')
    regex_groups = match_obj.groupdict()
    owner_id = int(regex_groups['owner_id'])
    owner_token = regex_groups['owner_token']
    opponent_id = int(regex_groups['opponent_id'])

    return owner_id, owner_token, opponent_id


def generate_dialog_tokens(owner_name: str, opponent_name: str):
    """
    Generates a new secret_key and tokens for each participant
    """
    secret_key = uuid4().hex
    expiry_date = get_utc_time() + timedelta(minutes=DIALOG_TOKEN_EXPIRY_MINUTES)
    owner_token = jwt.encode({'exp': expiry_date, 'username': owner_name}, secret_key)
    opponent_token = jwt.encode({'exp': expiry_date, 'username': opponent_name}, secret_key)

    return secret_key, owner_token, opponent_token


def get_utc_time():
    return datetime.utcnow()
