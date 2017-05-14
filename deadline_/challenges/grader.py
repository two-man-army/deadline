"""
The logic which grades input files is here. This file is intended to be ran solely from a Docker container,
where the input/output.txt files are in the same folder as the solution file with the code in it
"""

import os
import sys
import uuid
import subprocess
import json

# from constants import (
#     GRADER_TEST_RESULT_DESCRIPTION_KEY, GRADER_TEST_RESULT_SUCCESS_KEY, GRADER_TEST_RESULT_TIME_KEY,
#     GRADER_TEST_RESULT_ERROR_MESSAGE_KEY, GRADER_COMPILE_FAILURE,
#     SITE_ROOT, RUSTLANG_TIMEOUT_SECONDS, RUSTLANG_ERROR_MESSAGE_SNIPPET, TESTS_FOLDER_NAME, RUSTLANG_FILE_EXTENSION,
#     CPP_FILE_EXTENSION, CPP_TIMEOUT_SECONDS)
import os.path

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
MIN_SUBMISSION_INTERVAL_SECONDS = 10  # the minimum time a user must wait between submissions
MAX_TEST_RUN_SECONDS = 5  # the maximum time a Submission can run
TESTS_FOLDER_NAME = 'challenge_tests'  # the name of the folder which holds tests for challenges


RUSTLANG_NAME = 'Rust'
PYTHONLANG_NAME = 'Python'
CPPLANG_NAME = 'C++'
GOLANG_NAME = 'Go'

# Keys for the object returned by the grader's AsyncResult function
GRADER_TEST_RESULTS_RESULTS_KEY = 'results'
GRADER_TEST_RESULT_SUCCESS_KEY = 'success'
GRADER_TEST_RESULT_TIME_KEY = 'time'
GRADER_TEST_RESULT_DESCRIPTION_KEY = 'description'
GRADER_TEST_RESULT_TRACEBACK_KEY = 'traceback'
GRADER_TEST_RESULT_ERROR_MESSAGE_KEY = 'error_message'
GRADER_COMPILE_FAILURE = 'COMPILATION FAILED'

RUSTLANG_TIMEOUT_SECONDS = 5
RUSTLANG_COMPILE_ARGS = ['rustc']
# TODO: Maybe think of a smarter way to go on about this or at least limit user input
RUSTLANG_ERROR_MESSAGE_SNIPPET = 'error: aborting due to previous error'
RUSTLANG_ERROR_MESSAGE_SNIPPET_2 = 'error: incorrect close delimiter'
RUSTLANG_FILE_EXTENSION = '.rs'
RUSTLANG_UNFRIENDLY_ERROR_MESSAGE = "note: Run with `RUST_BACKTRACE=1`"  # error message that is of no interest to the user

CPP_TIMEOUT_SECONDS = 4
CPP_FILE_EXTENSION = '.cpp'
CPP_COMPILE_ARGS = ['g++', '-std=c++11', '-o']


PYTHON_TIMEOUT_SECONDS = 5
PYTHON_FILE_EXTENSION = '.py'
PYTHON_RUN_COMMAND = 'python3'

GO_TIMEOUT_SECONDS = 4
GO_FILE_EXTENSION = '.go'
GO_COMPILE_ARGS = ['go', 'build']


def main():
    """
    This main method is called exclusively while in the Docker container.
    Sample program usage - python3 grader.py {solution_file} {test_count} {language}
                        ex: python3 grader.py /home/solution.rs 5 Rust
    """
    LANGUAGE_GRADERS = {
        PYTHONLANG_NAME: PythonGrader,
        RUSTLANG_NAME: RustGrader,
        CPPLANG_NAME: CppGrader,
        GOLANG_NAME: GoGrader
    }
    solution_file = sys.argv[1]
    test_count = int(sys.argv[2])
    language = sys.argv[3]
    print(f'Language is {language}')
    grader = LANGUAGE_GRADERS[language](test_count, solution_file)

    # Print out the results so that the main program running docker can get the information
    print(grader.grade_solution())


class GraderTestCase:
    def __init__(self, input_lines: [str], expected_output_lines: [str]):
        self.input_lines = input_lines
        self.expected_output_lines = expected_output_lines


class BaseGrader:
    """
    Note: This is not functional on its own!

     Base Grader class which has information about
        the temp_file_name: ex: "solution.py", "solution.cpp" etc

    It has implemented methods that
        finds the tests for the given challenge (expected to be in the same folder and named by convention)
        reads the tests (and saves their contents in a input/output string lists)
        grades all the tests (by running the code and comparing the output to the expected output)
    """
    def __init__(self, test_case_count, temp_file_name):
        self.test_case_count = test_case_count

        self.test_folder_name = temp_file_name
        self.unique_name = temp_file_name

        self.temp_file_name = temp_file_name + self.FILE_EXTENSION
        self.temp_file_abs_path = os.path.join(SITE_ROOT, self.temp_file_name)
        self.read_input = None
        self.test_cases = []

    def grade_solution(self):
        """
        This function does the whole process of grading a submission
        This is up to each child class to increment itself
        """
        raise NotImplementedError()

    def run_program_process(self) -> subprocess.Popen:
        """
        :return: The process of the program. This is up to every grader to implement
        """
        raise NotImplementedError()

    def grade_all_tests(self) -> str:
        """
        This function goes through every input/output and runs an instance of the code for each.
        :returns A JSON string representing the results
        """
        overall_dict = {"results": []}

        for test_case in self.test_cases:
            test_case_result: dict = self.test_solution(test_case)
            overall_dict['results'].append(test_case_result)

        return json.dumps(overall_dict)

    def find_tests(self) -> [os.DirEntry]:
        """
        Find the tests and return two lists, one with the input files and the other with the output files,
            sorted by name
        """
        if not os.path.isdir(TESTS_FOLDER_NAME):
            raise Exception(f'The path {TESTS_FOLDER_NAME} is invalid!')

        # Read  the files in the directory
        input_files, output_files = [], []
        for file in os.scandir(TESTS_FOLDER_NAME):
            if file.name.startswith('input'):
                input_files.append(file)
            elif file.name.startswith('output'):
                output_files.append(file)
        print("#", input_files)
        print("#", output_files)
        files_len = len(input_files) + len(output_files)
        # There must be two files for every test case
        if files_len != (2*self.test_case_count) or files_len % 2 != 0:
            raise Exception('Invalid input/output file count!')

        return list(sorted(input_files, key=lambda file: file.name)), list(sorted(output_files, key=lambda file: file.name))

    def read_tests(self, sorted_input_files: [os.DirEntry], sorted_output_files: [os.DirEntry]):
        """
        Constructs a GraderTestCase object for each pairing input/output .txt file
        and
        Fills the self.test_cases list with said objects

        :param sorted_input_files: A list of all the input-xx.txt files, sorted by their name
        :param sorted_output_files: A list of all the output-xx.txt files, sorted by their name
        """
        self.test_cases = []
        inp_file_count, out_file_count = len(sorted_input_files), len(sorted_output_files)
        if inp_file_count != out_file_count:
            raise Exception(f'Input/Output files are not in pairs! '
                            f'\nInput:{inp_file_count}\nOutput:{out_file_count}')
        for input_file, output_file in zip(sorted_input_files, sorted_output_files):
            """ Since the files are sorted by name, an input file should be followed by an output file
                i.e  input-01.txt output-01.txt input-02.txt output-02.txt """
            if not input_file.name.startswith('input') or not output_file.name.startswith('output'):
                raise Exception('Invalid input/output file names when reading them.')

            with open(os.path.abspath(input_file.path)) as f:
                input_lines = [line.strip() for line in f.readlines()]
            with open(os.path.abspath(output_file.path)) as f:
                output_lines = [line.strip() for line in f.readlines()]

            self.test_cases.append(GraderTestCase(input_lines=input_lines, expected_output_lines=output_lines))

        self.read_input = True

    def cleanup_error_message(self, error_msg) -> str:
        """ Optionally remove some parts of the error message that you would not want to be displayed to the user """
        return error_msg

    def test_solution(self, test_case: GraderTestCase) -> dict:
        """
        Runs a single process to test a solution
        :param test_case:
        :return:
        """
        input_str = '\n'.join(test_case.input_lines)

        result_dict = {
            "error_message": "",
            "success": False,
            "time": "0",
            GRADER_TEST_RESULT_DESCRIPTION_KEY: f'Testing with {input_str}',
            'traceback': ""
        }

        # Run the program
        program_process = self.run_program_process()

        try:
            # Enter the input and wait for the response
            results = program_process.communicate(input=input_str.encode(), timeout=self.TIMEOUT_SECONDS)
            error_message = results[1].decode()
        except subprocess.TimeoutExpired:
            # TODO: Add timed_out bool and maybe attach it to error_message instead of traceback
            error_message = f'Timed out after {self.TIMEOUT_SECONDS} seconds'
            program_process.kill()

        if error_message:  # There is some error in the code
            result_dict["traceback"] = self.cleanup_error_message(error_message)
        else:  # Program has run successfully
            given_output = results[0].decode().strip()
            expected_output = '\n'.join(test_case.expected_output_lines)

            if given_output == expected_output:
                result_dict['success'] = True
            else:
                print(f'{given_output} is not equal to {expected_output}')
                result_dict['error_message'] = f"{given_output} is not equal to the expected {expected_output}"

        return result_dict


class CompilableLangGrader(BaseGrader):
    """
    The Grader for all languages that require compilation
    Additionally holds information for the
        executable file created - name and absolute path
        whether compilation was successful
    """
    def __init__(self, test_case_count, test_folder_name):
        super().__init__(test_case_count, test_folder_name)
        self.temp_exe_file_name = None
        self.temp_exe_abs_path = None
        self.compiled = False
        self.compile_error_message = None

    def grade_solution(self):
        """
        This function does the whole process of grading a submission
        """
        print('# Running solution')
        sorted_input_files, sorted_output_files = self.find_tests()
        print(f'# Found tests at {sorted_input_files} {sorted_output_files}')
        self.read_tests(sorted_input_files, sorted_output_files)
        print('# Compiling')
        self.compile()

        if self.compiled:
            result = self.grade_all_tests()
            return result
        else:
            print('# COULD NOT COMPILE')
            print(self.compile_error_message)
            return json.dumps({GRADER_COMPILE_FAILURE: self.compile_error_message})

    def compile(self):
        """
        Compiles the program
        """
        compiler_proc = subprocess.Popen(
            self.COMPILE_ARGS + [self.temp_file_abs_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        compile_result = compiler_proc.communicate()
        compiler_proc.kill()
        error_message = compile_result[1].decode()

        if not self.has_compiled(error_message):  # There is an error while compiling
            self.compiled = False
            self.compile_error_message = error_message
        else:
            self.compiled = True
            self.temp_exe_abs_path = os.path.join(SITE_ROOT, self.unique_name)

    def run_program_process(self):
        """ Start the program and return the process object. """
        return subprocess.Popen([self.temp_exe_abs_path],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def has_compiled(self, error_message) -> bool:
        """
        Return a boolean indicating whether compilation was successful
        Useful to override in the case of Rust where the compiler issues out warnings as error messages even
        if compilation was successful
        """
        return not bool(error_message)


class InterpretableLangGrader(BaseGrader):
    """ The Base Grader for all languages that are interpreted"""

    def grade_solution(self):
        """
        This function does the whole process of grading a submission
        """
        print('# Running solution')

        sorted_input_files, sorted_output_files = self.find_tests()
        print(f'# Found tests at {sorted_input_files} {sorted_output_files}')
        self.read_tests(sorted_input_files, sorted_output_files)  # fills variables with the input/expected output

        result = self.grade_all_tests()

        return result

    def run_program_process(self):
        return subprocess.Popen([self.RUN_COMMAND, self.temp_file_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)


class RustGrader(CompilableLangGrader):
    TIMEOUT_SECONDS = RUSTLANG_TIMEOUT_SECONDS
    FILE_EXTENSION = RUSTLANG_FILE_EXTENSION
    COMPILE_ARGS = RUSTLANG_COMPILE_ARGS

    def has_compiled(self, error_message) -> bool:
        """
        Return a boolean indicating whether compilation was successful
        """
        return not (bool(error_message) and (RUSTLANG_ERROR_MESSAGE_SNIPPET in error_message or RUSTLANG_ERROR_MESSAGE_SNIPPET_2 in error_message))

    def cleanup_error_message(self, error_msg) -> str:
        """ Removes unecessary information from a Rust error message, making it more user friendly"""
        if RUSTLANG_UNFRIENDLY_ERROR_MESSAGE in error_msg:
            error_msg = error_msg.replace(RUSTLANG_UNFRIENDLY_ERROR_MESSAGE, '')

        return error_msg


class CppGrader(CompilableLangGrader):
    TIMEOUT_SECONDS = CPP_TIMEOUT_SECONDS
    COMPILE_ARGS = CPP_COMPILE_ARGS
    FILE_EXTENSION = CPP_FILE_EXTENSION

    def compile(self):
        """
        Compiles the program
        """
        compiler_proc = subprocess.Popen(
            # need to specially tell it to compile to the same name
            self.COMPILE_ARGS + [self.unique_name, os.path.join(SITE_ROOT, self.temp_file_name)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        compile_result = compiler_proc.communicate()
        compiler_proc.kill()
        error_message = compile_result[1].decode()

        if not self.has_compiled(error_message):  # There is an error while compiling
            self.compiled = False
            self.compile_error_message = error_message
        else:
            self.compiled = True
            self.temp_exe_abs_path = os.path.join(SITE_ROOT, self.unique_name)


class GoGrader(CompilableLangGrader):
    TIMEOUT_SECONDS = GO_TIMEOUT_SECONDS
    COMPILE_ARGS = GO_COMPILE_ARGS
    FILE_EXTENSION = GO_FILE_EXTENSION


class PythonGrader(InterpretableLangGrader):
    """
    This is a sort of special class, since the
    """
    TIMEOUT_SECONDS = PYTHON_TIMEOUT_SECONDS
    FILE_EXTENSION = PYTHON_FILE_EXTENSION
    RUN_COMMAND = PYTHON_RUN_COMMAND


if __name__ == '__main__':
    main()
