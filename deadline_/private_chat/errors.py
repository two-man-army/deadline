from errors import Error


class RegexMatchError(Error):
    """ Used when we cannot match with regex """
    pass


class ChatPairingError(Error):
    pass


class UserTokenMatchError(Error):
    pass


class MaliciousUserException(Error):
    """ Used when a User is detected to have tried something malicious """
    pass
