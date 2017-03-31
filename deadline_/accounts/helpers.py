import hashlib


def hash_password(password, salt):
    return hashlib.sha512((password + salt).encode('utf-8')).hexdigest()