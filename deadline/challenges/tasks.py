import subprocess
import uuid
import os
import time

from challenges.models import Challenge, Submission
from challenges.helper import convert_to_normal_text
from constants import MAX_TEST_RUN_SECONDS
from deadline.celery import app

from challenges.grader import RustGrader


@app.task
def run_grader(test_file_name, code):
    """
    Runs a celery task for the grader, after which saves the result to the DB (by returning the value)
    """
    # create a temp file,
    temp_file_name = uuid.uuid4().hex + '.py'

    # write the code to it
    with open(temp_file_name, 'w') as temp_file:
        temp_file.write(code)
        temp_file.flush()
        os.fsync(temp_file.fileno())

    # run the grader
    proc = subprocess.Popen(
        ['python3', '-m', 'grader', '--sandbox', 'docker', 'challenge_tests/' + test_file_name + '.py', temp_file_name],
        stdout=subprocess.PIPE)

    # Remove the file after the max test time
    time.sleep(MAX_TEST_RUN_SECONDS)
    try:
        os.remove(temp_file_name)
    except OSError:
        pass

    output = proc.stdout.readlines()
    return convert_to_normal_text(output)

@app.task
def run_rust_grader(test_case_count, test_file_name, code):
    rg = RustGrader(test_case_count, test_file_name, code)
    return rg.run_solution()

