import subprocess
import uuid
import os
import json
import time

from challenges.models import Challenge, Submission
from challenges.helper import convert_to_normal_text
from constants import (MAX_TEST_RUN_SECONDS, PYTHONLANG_NAME, RUSTLANG_NAME, CPPLANG_NAME, DOCKER_CLIENT,
                       DOCKER_IMAGE_PATH, TESTS_FOLDER_NAME, SITE_ROOT, CHALLENGES_APP_FOLDER_NAME, GRADER_FILE_NAME,
                       GOLANG_NAME, KOTLIN_NAME)

from deadline.celery import app

from challenges.grader import RustGrader, PythonGrader, CppGrader, BaseGrader, GoGrader, KotlinGrader

from challenges.helper import delete_file

LANGUAGE_GRADERS = {
    PYTHONLANG_NAME: PythonGrader,
    RUSTLANG_NAME: RustGrader,
    CPPLANG_NAME: CppGrader,
    GOLANG_NAME: GoGrader,
    KOTLIN_NAME: KotlinGrader
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


def run_grader(test_case_count, test_folder_name, code, lang) -> dict:
    """
    Given
        :param test_case_count: The number of test cases for the challenge
        :param test_folder_name: The folder where said test cases reside
        :param code: The solution's code
        :param lang: The language the solution's code is in
    builds a Docker image, copies over relevant information so that the image can run grader.py and
    actually grade the solution and returns the results
    :return:
    """
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

    docker_command = (
        f"docker run -d"  # run docker and get the ID of the container
        f" -v {challenge_tests_folder_abs_path}:{destination_tests_folder}:ro"  # copy the test .txt files over
        f" -v {grader_file_abs_path}:{destination_grader_abs_path}"  # copy grader.py over
        f" -v {temp_file_abs_path}:{destination_temp_file_abs_path}"  # copy the file with the code in it over
        # select the image and run grader.py in it with the arguments {solution path} {test case count} {language}
        f" {docker_image.id} python {destination_grader_abs_path} sol {test_case_count} {lang}")

    docker_id_ps_res: tuple = subprocess.Popen(docker_command.split(),
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    if docker_id_ps_res[1] != b'':
        raise Exception(f'Error while running the container: {docker_id_ps_res[1]}')

    docker_id = docker_id_ps_res[0].decode()

    process_results: tuple = subprocess.Popen(  # attach to the container and read the results
        f'docker attach --sig-proxy=false {docker_id}'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if process_results[1] != b'':
        raise Exception(f'Error while attaching to docker container {docker_id}.\n{process_results[1].decode()}')

    results: str = process_results[0].decode().split('\n')[-2]

    # remove the docker container and the file with code
    subprocess.Popen(f'docker rm -f {docker_id}'.split()).communicate()
    delete_file(temp_file_name)

    return json.loads(results)

@app.task
def run_grader_task(test_case_count, test_folder_name, code, lang) -> dict:
    """
    Runs a celery task for the grader, after which saves the result to the DB (by returning the value)
    Note: The Grader runs in Docker and prints out the results in a JSON format at the end.
          That is why we get them by accessing [-2] from the stdout output
    """
    return run_grader(test_case_count, test_folder_name, code, lang)