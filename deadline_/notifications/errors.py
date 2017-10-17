from errors import Error


class NotificationAlreadyRead(Error):
    """ Used when a notification is already read and it makes no sense to send it to the user """
    pass


class OfflineRecipientError(Error):
    """ Used when we try to access the connection of a recipient that has not connected"""
    pass


class InvalidNotificationToken(Error):
    """ Used when the user tries to authenticate with a notification token that is not his """
    pass


class RecipientMismatchError(Error):
    """ Used when a user tries to read a notification that is not his """
    pass


class MaliciousUserException(Error):
    """ Used when a User is detected to have tried something malicious """
    pass
