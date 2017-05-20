from django.utils.deconstruct import deconstructible
from django.core.validators import BaseValidator

from collections.abc import Iterable


@deconstructible
class MaxFloatDigitValidator(BaseValidator):
    message = 'Ensure the digits after the float are less than or equal to %(max_floating_digits)s.'
    code = 'max_floating_digits'

    def compare(self, given_float, max_digit_count):
        given_float = str(given_float)
        try:
            return len(given_float[given_float.index('.') + 1:]) > max_digit_count
        except ValueError:
            return False  # no floating digits


@deconstructible
class PossibleFloatDigitValidator(BaseValidator):
    """
    Given a list of valid floating digits, ensure that the float numbers have them exactly

    Used to validate our Challenge's difficulty field, as it can be 1.0, 1.5, 2.0, 2.5 and etc
    """
    message = 'Ensure the digits after the float are equal to at least one %(possible_floats)s.'
    code = 'possible_floats'

    def compare(self, given_float, possible_digits):
        if not isinstance(possible_digits, Iterable):
            raise Exception("PossibleFloatDigitValidator takes an iterable collection as an argument!")
        # convert the digits to string in case
        for idx, val in enumerate(possible_digits):
            possible_digits[idx] = str(val)

        given_float = str(given_float)
        try:
            floating_digits = given_float[given_float.index('.') + 1:]
            return floating_digits not in possible_digits
        except ValueError:
            return False  # no floating digits
