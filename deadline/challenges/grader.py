import os
import uuid
import subprocess

from challenges.models import Submission, Challenge
TESTS_LOCATION = 'challenge_tests/rust/'


class RustGrader:
    """
    Takes a Challenge and Solution object
     Finds its tests
     Compiles the program
     Runs it for each tests
     Returns the grades
    """
    def __init__(self, challenge: Challenge, solution: Submission):
        self.challenge = challenge
        self.solution = solution
        self.test_cases = []
        self.tests_folder = None
        self.temp_file_name = None
        self.read_input = False
        self.compiled = False

        self.create_solution_file()
        sorted_files = self.find_tests()
        self.read_tests(sorted_files)
        self.compile()
        self.delete_solution_file()
        if self.compiled:
            pass

    def compile(self):
        # TODO: Docker?
        compiler_proc = subprocess.Popen(
            ['rustc', self.temp_file_name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        compile_result = compiler_proc.communicate()
        error_message = compile_result[1].decode()
        if error_message:
            # There is an error while compiling
            self.compiled = False
            # update the solution
            self.solution.compiled = False
            self.solution.compile_error_message = error_message
            self.solution.save()
        else:
            self.compiled = True

    def grade_solution(self):
        """ This function goes through every input/output and runs an instance of the code for each."""
        raise NotImplementedError()


    def find_tests(self) -> [os.DirEntry]:
        """
        Find the tests and return all of them in a list sorted by their name
        :return:
        """
        self.tests_folder: str = os.path.join(TESTS_LOCATION, self.challenge.name)
        if not os.path.isdir(self.tests_folder):
            raise Exception(f'The path {self.tests_folder} is invalid!')
        files = []

        # Read  the files in the directory
        for file in os.scandir(self.tests_folder):
            if file.name.startswith('input') or file.name.startswith('output'):
                files.append(file)

        # There must be two files for every test case
        if len(files) != (2*self.challenge.test_case_count) or len(files) % 2 != 0:
            raise Exception('Invalid input/output file count!')

        return list(sorted(files, key=lambda file: file.name))

    def read_tests(self, sorted_files):
        idx = 0

        while idx < len(sorted_files):
            # Since the files are sorted by name, an input file should be followed by an output file
            input_lines, output_lines = [], []
            input_file = sorted_files[idx]
            output_file = sorted_files[idx + 1]

            if 'input' not in input_file.name or 'output' not in output_file.name:
                raise Exception('Invalid input/output file names when reading them.')

            with open(os.path.abspath(input_file.path)) as f:
                input_lines = [line.strip() for line in f.readlines()]
            with open(os.path.abspath(output_file.path)) as f:
                output_lines = [line.strip() for line in f.readlines()]
            idx += 2

            self.test_cases.append(RustTestCase(input_lines=input_lines, expected_output_lines=output_lines))

        self.read_input = True

    def create_solution_file(self):
        """ Creates a temporary file which will represent the code """
        self.temp_file_name = uuid.uuid4().hex + '.rs'

        # write the code to it
        with open(self.temp_file_name, 'w') as  temp_file:
            temp_file.write(self.solution.code)
            temp_file.flush()
            os.fsync(temp_file.fileno())

    def delete_solution_file(self):
        try:
            os.remove(self.temp_file_name)
        except OSError:
            pass


class RustTestCase:
    def __init__(self, input_lines: [str], expected_output_lines: [str]):
        self.input_lines = input_lines
        self.expected_output_lines = expected_output_lines
