"""
Universal errors that are used across the apps
"""


class Error(Exception):
    pass


class ForbiddenMethodError(Error):
    """ For methods which are not intended to be used. e.g Notification.objects.create method"""
    pass


class FetchError(Exception):
    pass


class DisabledSerializerError(Exception):
    pass
