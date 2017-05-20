from unittest import TestCase  # no need to use overbloated django testcase here

from django.core.exceptions import ValidationError

from challenges.validators import MaxFloatDigitValidator, PossibleFloatDigitValidator


class MaxFloatDigitTests(TestCase):
    def test_valid_integers(self):
        validator = MaxFloatDigitValidator(limit_value=0)

        valid_integers = list(range(11))
        for valid_int in valid_integers:
            validator(valid_int)  # sould not raise

    def test_valid_floats(self):
        validator = MaxFloatDigitValidator(limit_value=1)

        valid_floats = [1.2, 3.3, 10.3, 10000.1, 0.3]
        for valid_float in valid_floats:
            validator(valid_float)  # should not raise

    def test_invalid_floats(self):
        validator = MaxFloatDigitValidator(limit_value=1)

        invalid_floats = [1.22, 1.333, 1000.111, 34141.41413414141]
        for invalid_float in invalid_floats:
            with self.assertRaises(ValidationError):
                validator(invalid_float)


class PossibleFloatDigitTests(TestCase):
    def test_invalid_integers(self):
        validator = PossibleFloatDigitValidator(['1', '2', '3'])
        # since we've not specified 0, all should be invalid

        for invalid_int in range(10):
            with self.assertRaises(ValidationError):
                validator(invalid_int)

    def test_validator_raises_error_on_non_iter_argument(self):
        with self.assertRaises(Exception):
            PossibleFloatDigitValidator(1)

    def test_validator_raises_error_on_non_string_iter_value(self):
        with self.assertRaises(Exception):
            PossibleFloatDigitValidator(['1', '12313', 4, '12'])

    def test_invalid_floats(self):
        validator = PossibleFloatDigitValidator(['11', '1', '111'])
        invalid_floats = [1.01, 1.113, 1.1111, 000.21, 1]
        for invalid_float in invalid_floats:
            with self.assertRaises(ValidationError):
                validator(invalid_float)

    def test_valid_floats(self):
        validator = PossibleFloatDigitValidator(['11', '1', '111', '0', '01'])
        valid_floats = [1.1, 4134141.11, 4134.1, 5, 5.01]
        for valid_float in valid_floats:
            validator(valid_float)  # should not raise
