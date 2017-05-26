"""
Helper functions for testing
TODO: Maybe create a base TestCase class
which inherits from others and attaches helpers there
    Problem with that: We use unitteset.TestCase, django.TestCase and APITestCase
"""


def get_mock_function_arguments(mock_fn) -> []:
    """
    Given a mocked function, return all the arguments it has received.
    This is needed, because the .assert_called_once_with() distinguishes between
    normal arg calls fn(1) and kwarg calls fn(num=1).
    This simply extracts all the values, so if we had a function
        fn('tank', num=2)
    This will return
        ['tank', 2]
    :param mock_fn: type: unittest.mock.MagicMock
    :return a list of the arguments
    """
    args, kwargs = mock_fn.call_args
    argument_values = list(args) + list(kwargs.values())
    return argument_values
