import subprocess
import uuid
import os
import time
from deadline.celery import app
from challenges.models import Challenge, Submission


@app.task
def run_grader(test_file_name, code):
    """
    Runs a celery task for the grader, after which saves the result to the DB (by returning the value)
    """
    def convert_to_normal_text(lines: list):
        """ Given a list with byte strings with a new-line at the end, return a concatenated string """
        return ''.join([st.decode('utf-8') for st in lines])

    # create temp file, write the code to it
    temp_file_name = uuid.uuid4().hex + '.py'

    with open(temp_file_name, 'w') as temp_file:
        temp_file.write(code)
        temp_file.flush()
        os.fsync(temp_file.fileno())

    # run the grader
    proc: subprocess.CompletedProcess = subprocess.Popen(
        ['python3', '-m', 'grader', 'challenge_tests/' + test_file_name + '.py', temp_file_name],
        stdout=subprocess.PIPE)

    # Remove the file after the max test time
    time.sleep(5)
    try:
        os.remove(temp_file_name)
    except OSError:
        pass

    output = proc.stdout.readlines()
    return convert_to_normal_text(output)