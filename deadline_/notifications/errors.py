from errors import Error


class NotificationAlreadyRead(Error):
    """ Used when a notification is already read and it makes no sense to send it to the user """
    pass


class OfflineRecipientError(Error):
    """ Used when we try to access the connection of a recipient that has not connected"""
    pass
