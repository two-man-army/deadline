class InvalidNewsfeedItemType(Exception):
    """ Used for when a somebody tries to create a Newsfeed Item with an invalid type """
    pass


class MissingNewsfeedItemContentField(Exception):
    """ Used for when a field is missing from NewsfeedItem's content field """
    pass


class InvalidNewsfeedItemContentField(Exception):
    """ Used for when a field which is not part of the NewsfeedItem's expected content fields
        is added to it regardless """
    pass
