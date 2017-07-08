class InvalidEnrollmentError(Exception):
    pass


class InvalidLockError(Exception):
    """ Used for when we cannot 'lock' (set is_under_construction to false) for some reason """
    pass


class AlreadyLockedError(Exception):
    """ Used for when a model that uses locks (is_under_construction) is already locked """
    pass


class StudentAlreadyEnrolledError(Exception):
    pass
