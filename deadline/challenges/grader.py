import os
import uuid
import subprocess
import json

from constants import (
    GRADER_TEST_RESULT_DESCRIPTION_KEY, GRADER_TEST_RESULT_SUCCESS_KEY, GRADER_TEST_RESULT_TIME_KEY,
    GRADER_TEST_RESULT_ERROR_MESSAGE_KEY, GRADER_COMPILE_FAILURE,
    SITE_ROOT)
from challenges.helper import delete_file
from challenges.helper import cleanup_rust_error_message
from challenges.models import Submission, Challenge
TESTS_LOCATION = 'challenge_tests/rust/'


# TODO: Improve class architecture!
class RustTestCase:
    def __init__(self, input_lines: [str], expected_output_lines: [str]):
        self.input_lines = input_lines
        self.expected_output_lines = expected_output_lines


class RustGrader:
    """
    Takes a Challenge and Solution object
     Finds its tests
     Compiles the program
     Runs it for each tests
     Returns the grades
    """
    def __init__(self, test_case_count, test_file_name, code: str):
        self.test_case_count = test_case_count
        self.test_file_name = test_file_name
        self.code = code
        self.test_cases = []
        self.tests_folder = None
        self.temp_file_name = None
        self.temp_file_abs_path = None
        self.temp_exe_file_name = None
        self.temp_exe_abs_path = None
        self.read_input = False
        self.compiled = False

    def run_solution(self):
        print('Running solution')
        self.create_solution_file()
        sorted_input_files, sorted_output_files = self.find_tests()
        print(f'Found tests at {sorted_input_files} {sorted_output_files}')
        self.read_tests(sorted_input_files, sorted_output_files)
        print('Compiling')
        self.compile()
        delete_file(self.temp_file_abs_path)
        # self.delete_solution_file(self.temp_file_name)

        if self.compiled:
            result = self.grade_solution()
            # self.delete_solution_file(self.temp_exe_file_name)
            delete_file(self.temp_exe_abs_path)

            return result
        else:
            print('COULD NOT COMPILE')
            print(self.compile_error_message)
            return {GRADER_COMPILE_FAILURE: self.compile_error_message}

    def compile(self):
        # TODO: Docker?
        compiler_proc = subprocess.Popen(
            ['rustc', self.temp_file_name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        compile_result = compiler_proc.communicate()
        compiler_proc.kill()
        error_message = compile_result[1].decode()
        if error_message and 'error: aborting due to previous error' in error_message:
            # There is an error while compiling
            self.compiled = False
            # update the solution
            # self.solution.compiled = False
            self.compile_error_message = error_message
            # self.solution.save()
        else:
            self.compiled = True

    def grade_solution(self):
        """ This function goes through every input/output and runs an instance of the code for each."""
        overall_dict = {"results": []}

        for test_case in self.test_cases:
            test_case_result: dict = self.test_solution(test_case)
            overall_dict['results'].append(test_case_result)
        return json.dumps(overall_dict)

    def test_solution(self, test_case: RustTestCase) -> dict:
        # TODO: Docker
        # TODO: Timer
        program_process = subprocess.Popen([self.temp_exe_abs_path],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Enter the input
        input_str = '\n'.join(test_case.input_lines)
        results = program_process.communicate(input=input_str.encode())

        result_dict = {
            "error_message": "",
            "success": False,
            "time": "0",
            GRADER_TEST_RESULT_DESCRIPTION_KEY: f'Testing with {input_str}',
            'traceback': ""
        }

        error_message = results[1].decode()
        if error_message:
            # There is some error in the code
            result_dict["traceback"] = cleanup_rust_error_message(error_message)
        else:
            # Program has run successfully
            given_output = results[0].decode().strip()
            expected_output = '\n'.join(test_case.expected_output_lines)

            if given_output == expected_output:
                result_dict['success'] = True
            else:
                print(f'{given_output} is not equal to {expected_output}')
                result_dict['error_message'] = f"{given_output} is not equal to the expected {expected_output}"

        return result_dict

    def find_tests(self) -> [os.DirEntry]:
        """
        Find the tests and return all of them in a list sorted by their name
        :return:
        """
        self.tests_folder: str = os.path.join(TESTS_LOCATION, self.test_file_name)
        if not os.path.isdir(self.tests_folder):
            raise Exception(f'The path {self.tests_folder} is invalid!')

        # Read  the files in the directory
        input_files, output_files = [], []
        for file in os.scandir(self.tests_folder):
            if file.name.startswith('input'):
                input_files.append(file)
            elif file.name.startswith('output'):
                output_files.append(file)

        # There must be two files for every test case
        files_len = len(input_files) + len(output_files)
        if files_len != (2*self.test_case_count) or files_len % 2 != 0:
            raise Exception('Invalid input/output file count!')

        return list(sorted(input_files, key=lambda file: file.name)), list(sorted(output_files, key=lambda file: file.name))

    def read_tests(self, sorted_input_files, sorted_output_files):
        inp_file_count, out_file_count = len(sorted_input_files), len(sorted_output_files)
        if inp_file_count != out_file_count:
            raise Exception(f'Input/Output files have different lengths! \nInput:{inp_file_count}\nOutput:{out_file_count}')

        for idx in range(inp_file_count):
            """ Since the files are sorted by name, an input file should be followed by an output file
                i.e  input-01.txt output-01.txt input-02.txt output-02.txt """
            input_file = sorted_input_files[idx]
            output_file = sorted_output_files[idx]

            if 'input' not in input_file.name or 'output' not in output_file.name:
                raise Exception('Invalid input/output file names when reading them.')

            with open(os.path.abspath(input_file.path)) as f:
                input_lines = [line.strip() for line in f.readlines()]
            with open(os.path.abspath(output_file.path)) as f:
                output_lines = [line.strip() for line in f.readlines()]

            self.test_cases.append(RustTestCase(input_lines=input_lines, expected_output_lines=output_lines))

        self.read_input = True

    def create_solution_file(self):
        """ Creates a temporary file which will represent the code """
        # Create a unique file name and their paths for later deletion
        self.temp_exe_file_name = uuid.uuid4().hex
        self.temp_exe_abs_path = os.path.join(SITE_ROOT, self.temp_exe_file_name)
        self.temp_file_name = self.temp_exe_file_name + '.rs'
        self.temp_file_abs_path = os.path.join(SITE_ROOT, self.temp_file_name)

        # write the code to it
        with open(self.temp_file_name, 'w') as temp_file:
            temp_file.write(self.code)
            temp_file.flush()
            os.fsync(temp_file.fileno())




