import hashlib
import jwt
from datetime import datetime, timedelta

from accounts.constants import NOTIFICATION_TOKEN_EXPIRY_MINUTES, NOTIFICATION_SECRET_KEY


def get_utc_time():
    return datetime.utcnow()


def generate_notification_token(user):
    """
    Generates a new notification token for a given user
    """
    expiry_date = get_utc_time() + timedelta(minutes=NOTIFICATION_TOKEN_EXPIRY_MINUTES)
    notification_token = jwt.encode({'exp': expiry_date, 'username': user.username}, NOTIFICATION_SECRET_KEY).decode("utf-8")

    return notification_token


def hash_password(password, salt):
    return hashlib.sha512((password + salt).encode('utf-8')).hexdigest()