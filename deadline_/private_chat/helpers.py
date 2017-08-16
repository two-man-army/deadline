import re

from private_chat.constants import CONNECT_PATH_REGEX
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
