import os.path
import docker
DOCKER_CLIENT = docker.from_env()
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))  # this is where the constants.py file should be
DOCKER_IMAGE_PATH = ROOT_PATH
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
MIN_SUBMISSION_INTERVAL_SECONDS = 10  # the minimum time a user must wait between submissions
MAX_TEST_RUN_SECONDS = 5  # the maximum time a Submission can run
TESTS_FOLDER_NAME = 'challenge_tests'  # the name of the folder which holds tests for challenges

CHALLENGES_APP_FOLDER_NAME = 'challenges'
GRADER_FILE_NAME = 'grader.py'  # the file which is sent over to the docker container and executed there

RUSTLANG_NAME = 'Rust'
PYTHONLANG_NAME = 'Python'
CPPLANG_NAME = 'C++'

# Keys for the object returned by the grader's AsyncResult function
GRADER_TEST_RESULTS_RESULTS_KEY = 'results'
GRADER_TEST_RESULT_SUCCESS_KEY = 'success'
GRADER_TEST_RESULT_TIME_KEY = 'time'
GRADER_TEST_RESULT_DESCRIPTION_KEY = 'description'
GRADER_TEST_RESULT_TRACEBACK_KEY = 'traceback'
GRADER_TEST_RESULT_ERROR_MESSAGE_KEY = 'error_message'
GRADER_COMPILE_FAILURE = 'COMPILATION FAILED'

RUSTLANG_TIMEOUT_SECONDS = 5
RUSTLANG_ERROR_MESSAGE_SNIPPET = 'error: aborting due to previous error'
RUSTLANG_ERROR_MESSAGE_SNIPPET_2 = 'error: incorrect close delimiter'
RUSTLANG_UNFRIENDLY_ERROR_MESSAGE = "note: Run with `RUST_BACKTRACE=1`"  # error message that is of no interest to the user
RUSTLANG_FILE_EXTENSION = '.rs'
RUSTLANG_COMPILE_ARGS = ['rustc']


CPP_TIMEOUT_SECONDS = 4
CPP_FILE_EXTENSION = '.cpp'
CPP_COMPILE_ARGS = ['g++', '-std=c++11', '-o']

PYTHON_TIMEOUT_SECONDS = 5
PYTHON_FILE_EXTENSION = '.py'
PYTHON_RUN_COMMAND = 'python3'