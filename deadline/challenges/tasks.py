import subprocess
import uuid
import os
import time

from challenges.models import Challenge, Submission
from challenges.helper import convert_to_normal_text
from constants import MAX_TEST_RUN_SECONDS, PYTHONLANG_NAME, RUSTLANG_NAME
from deadline.celery import app

from challenges.grader import RustGrader, PythonGrader


@app.task
def run_grader(test_case_count, test_folder_name, code, lang):
    """
    Runs a celery task for the grader, after which saves the result to the DB (by returning the value)
    """
    result = None

    if lang == PYTHONLANG_NAME:
        result = PythonGrader(test_case_count, test_folder_name, code).grade_solution()
    elif lang == RUSTLANG_NAME:
        result = RustGrader(test_case_count, test_folder_name, code).grade_solution()
    else:
        raise Exception(f'{lang} is not a supported language!')

    return result

