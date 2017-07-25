class UserAlreadyFollowedError(Exception):
    """ Used for when a User tries to follow a User he has already followed """
    pass


class UserNotFollowedError(Exception):
    """ Used for when a User tries to unfollow a User he has not followed """
    pass
