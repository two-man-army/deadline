from grader import *


@test_cases(['Hello World'], description='Searching for word {0}')
def search(m, wanted_str):
    output = m.stdout.new()
    assert wanted_str in output, '{0} not in {1}'.format(wanted_str, output)