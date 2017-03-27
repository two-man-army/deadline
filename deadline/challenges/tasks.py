import subprocess
import uuid
import os
import time

from challenges.models import Challenge, Submission
from challenges.helper import convert_to_normal_text
from constants import MAX_TEST_RUN_SECONDS, PYTHONLANG_NAME, RUSTLANG_NAME, CPPLANG_NAME
from deadline.celery import app

from challenges.grader import RustGrader, PythonGrader, CppGrader

from challenges.helper import delete_file


def create_temp_file(code: str) -> str:
    """ Creates a temporary file which will represent the code """
    import uuid
    unique_name = uuid.uuid4().hex
    temp_file_name = unique_name

    with open(temp_file_name, 'w') as temp_file:
        temp_file.write(code)
        temp_file.flush()
        os.fsync(temp_file.fileno())

    return temp_file_name

@app.task
def run_grader(test_case_count, test_folder_name, code, lang):
    """
    Runs a celery task for the grader, after which saves the result to the DB (by returning the value)
    """
    result = None
    temp_file_name = create_temp_file(code)

    docker_command = "docker run -d -v /home/netherblood/PycharmProjects/two-man-army/deadline/deadline/challenge_tests/" + test_folder_name + "/:/tests" \
                    " -v /home/netherblood/PycharmProjects/two-man-army/deadline/deadline/challenges/grader.py:/tests/grader.py" \
                    " -v /home/netherblood/PycharmProjects/two-man-army/deadline/deadline/" + temp_file_name + ":/tests/sol.py " \
                   "python:latest python /tests/grader.py sol.py " + str(test_case_count)
    print(docker_command)
    import subprocess

    ps = subprocess.Popen(docker_command.split(), stdout=subprocess.PIPE)
    docker_id = ps.communicate('')[0].decode()
    print(docker_id)
    print(docker_id)
    print(docker_id)
    ps = subprocess.Popen(f'docker attach --sig-proxy=false {docker_id}'.split(), stdout=subprocess.PIPE)
    # ps = subprocess.Popen([docker_command], stdout=subprocess.PIPE)
    results: str = ps.communicate('')[0].decode().split('\n')[-2]
    # print(ps.communicate('')[1].split('\n'))
    # result = '\n'.join(filter(lambda x: not x.startswith('#'), ps.communicate('')[0].split('\n')))
    print(results)
    # remove the docker container
    print(subprocess.Popen(f'docker rm -f {docker_id}'.split()).communicate())

    delete_file(temp_file_name)
    # TODO: Maybe associate each name with the language in a dict
    # if lang == PYTHONLANG_NAME:
    #     result = PythonGrader(test_case_count, test_folder_name, code).grade_solution()
    # elif lang == RUSTLANG_NAME:
    #     result = RustGrader(test_case_count, test_folder_name, code).grade_solution()
    # elif lang == CPPLANG_NAME:
    #     result = CppGrader(test_case_count, test_folder_name, code).grade_solution()
    # else:
    #     raise Exception(f'{lang} is not a supported language!')
    import json
    results = json.loads(results)
    print(type(results))
    return results

