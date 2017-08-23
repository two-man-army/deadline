"""
Universal errors that are used across the apps
"""
class Error(Exception):
    pass


class FetchError(Exception):
    pass


class DisabledSerializerError(Exception):
    pass
