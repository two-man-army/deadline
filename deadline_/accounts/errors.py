from social.errors import InvalidFollowError


class UserAlreadyFollowedError(InvalidFollowError):
    """ Used for when a User tries to follow a User he has already followed """
    pass


class UserNotFollowedError(InvalidFollowError):
    """ Used for when a User tries to unfollow a User he has not followed """
    pass
