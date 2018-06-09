from rest_framework.exceptions import APIException


class InvalidDateModeException(APIException):
    status_code = 400
    default_detail = 'Date mode {date_mode} is not supported!'
    default_code = 'error'

    def __init__(self, date_mode):
        self.detail = self.default_detail.format(date_mode=date_mode)
