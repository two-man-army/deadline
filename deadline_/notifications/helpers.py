import re

from private_chat.errors import RegexMatchError

CONNECT_PATH_REGEX = r'^\/notifications\/(?P<user_id>\d{1,})\/subscribe$'


def extract_connect_path(path) -> int:
    """
    Sample path: /notifications/{user_id}/subscribe
    """
    match_obj = re.match(CONNECT_PATH_REGEX, path)
    if match_obj is None:
        raise RegexMatchError(f'Path {path} does not match the expected regex!')
    return int(match_obj.groupdict()['user_id'])
