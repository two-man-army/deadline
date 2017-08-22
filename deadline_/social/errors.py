class InvalidNewsfeedItemType(Exception):
    """ Used for when a somebody tries to create a Newsfeed Item with an invalid type """
    pass


class InvalidNotificationType(Exception):
    """ Used for when a somebody tries to create a Notification with an invalid type """
    pass


class MissingNewsfeedItemContentField(Exception):
    """ Used for when a field is missing from NewsfeedItem's content field """
    pass


class MissingNotificationContentField(Exception):
    """ Used for when a field is missing from Notification's content field """
    pass


class InvalidNewsfeedItemContentField(Exception):
    """ Used for when a field which is not part of the NewsfeedItem's expected content fields
        is added to it regardless """
    pass


class InvalidNotificationContentField(Exception):
    """ Used for when a field which is not part of the Notification's expected content fields
        is added to it regardless """
    pass


class LikeAlreadyExistsError(Exception):
    """ Used for when a User tries to create a Like but it already exists """
    pass


class NonExistentLikeError(Exception):
    """ Used for when a User tries to delete a Like but it does not exist in the first place """
    pass
