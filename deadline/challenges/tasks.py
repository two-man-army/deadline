import subprocess
import uuid
import os
import json
import time

from challenges.models import Challenge, Submission
from challenges.helper import convert_to_normal_text
from constants import (MAX_TEST_RUN_SECONDS, PYTHONLANG_NAME, RUSTLANG_NAME, CPPLANG_NAME, DOCKER_CLIENT,
                       DOCKER_IMAGE_PATH, TESTS_FOLDER_NAME, SITE_ROOT, CHALLENGES_APP_FOLDER_NAME, GRADER_FILE_NAME)

from deadline.celery import app

from challenges.grader import RustGrader, PythonGrader, CppGrader, BaseGrader

from challenges.helper import delete_file

LANGUAGE_GRADERS = {
    PYTHONLANG_NAME: PythonGrader,
    RUSTLANG_NAME: RustGrader,
    CPPLANG_NAME: CppGrader
}


def create_temp_file(code: str) -> (str, str):
    """
    Creates a temporary file which will represent the code
    Returns the file name and the absolute path to it
    """
    unique_name = uuid.uuid4().hex
    temp_file_name = unique_name

    with open(temp_file_name, 'w') as temp_file:
        temp_file.write(code)
        temp_file.flush()
        os.fsync(temp_file.fileno())

    return temp_file_name, os.path.join(SITE_ROOT, temp_file_name)


@app.task
def run_grader(test_case_count, test_folder_name, code, lang):
    """
    Runs a celery task for the grader, after which saves the result to the DB (by returning the value)
    """
    # maybe wrap the logic here in another function that is not a Celery task and therefore testable
    if lang not in LANGUAGE_GRADERS:
        raise Exception(f'{lang} is not a supported language!')

    docker_image = DOCKER_CLIENT.images.build(path=DOCKER_IMAGE_PATH)
    grader: BaseGrader = LANGUAGE_GRADERS[lang]

    temp_file_name, temp_file_abs_path = create_temp_file(code)  # creates a temp file with the code in it

    challenge_tests_folder_abs_path = os.path.join(SITE_ROOT, TESTS_FOLDER_NAME, test_folder_name)
    destination_tests_folder = os.path.join('/', TESTS_FOLDER_NAME)  # the folder on the docker container with the tests

    grader_file_abs_path = os.path.join(SITE_ROOT, CHALLENGES_APP_FOLDER_NAME, GRADER_FILE_NAME)

    destination_grader_abs_path = os.path.join('/', GRADER_FILE_NAME)
    destination_temp_file_abs_path = os.path.join('/', 'sol' + grader.FILE_EXTENSION)
    print(destination_temp_file_abs_path)
    docker_command = (f"docker run -d"  # run docker and get the ID of the container
                      f" -v {challenge_tests_folder_abs_path}:{destination_tests_folder}:ro"
                      f" -v {grader_file_abs_path}:{destination_grader_abs_path}"
                      f" -v {temp_file_abs_path}:{destination_temp_file_abs_path}"
                      f" {docker_image.id} python {destination_grader_abs_path} sol {test_case_count} {lang}")

    ps = subprocess.Popen(docker_command.split(), stdout=subprocess.PIPE)
    docker_id = ps.communicate()[0].decode()
    ps = subprocess.Popen(f'docker attach --sig-proxy=false {docker_id}'.split(), stdout=subprocess.PIPE)
    all_results = ps.communicate()
    results: str = all_results[0].decode().split('\n')[-2]
    # remove the docker container
    subprocess.Popen(f'docker rm -f {docker_id}'.split()).communicate()
    delete_file(temp_file_name)

    results = json.loads(results)
    return results

