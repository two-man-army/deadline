from errors import Error


class RegexMatchError(Error):
    """ Used when we cannot match with regex """
    pass


class ChatPairingError(Error):
    pass


class UserTokenMatchError(Error):
    pass
