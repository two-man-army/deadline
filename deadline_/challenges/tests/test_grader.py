import json
from unittest.mock import MagicMock, Mock, patch, mock_open
import subprocess

from django.test import TestCase

from constants import TESTS_FOLDER_NAME, GRADER_COMPILE_FAILURE
from challenges.grader import RustGrader, GraderTestCase, BaseGrader, CompilableLangGrader, InterpretableLangGrader, CppGrader, PythonGrader, KotlinGrader


class DirEntryMock(Mock):
    def __init__(self, name, path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.path = path

    def __lt__(self, other):
        return self.name < other.name


class BaseGraderTests(TestCase):
    def setUp(self):
        BaseGrader.FILE_EXTENSION = '.test'
        self.test_case_count = 2
        self.temp_file_name = 'testfile.txt'
        self.grader = BaseGrader(self.test_case_count, self.temp_file_name)
        self.grader.RUN_ARGS = ['']
        # MagicMock.__gt__ = lambda x, y: x.name > y.name
        self.input_files_dir_entries = [DirEntryMock(name='input-01.txt'), DirEntryMock(name='input-02.txt'),
                                        DirEntryMock(name='output-01.txt'), DirEntryMock(name='output-02.txt')]

    @patch('challenges.grader.BaseGrader.test_solution')
    @patch('challenges.grader.get_seconds_duration')
    def test_grade_all_tests(self, mocked_get_duration, mocked_test_solution):
        """ Method should go through every input/output and run self.test_solution() for it """
        mocked_get_duration.return_value = 155
        mocked_test_solution.return_value = 42
        self.grader.test_cases = [None] * 10  # 10 empty items

        # should basically call test_solution 10 times
        expected_result = {'results': [42] * 10, 'elapsed_seconds': 155}
        self.assertEqual(self.grader.grade_all_tests(), json.dumps(expected_result))

    @patch('challenges.grader.os.path.isdir')
    @patch('challenges.grader.os.scandir')
    def test_find_tests_works_correctly(self, scandir_mock, isdir_mock):
        isdir_mock.return_value = True
        scandir_mock.return_value = self.input_files_dir_entries

        received_input_files, received_output_files = self.grader.find_tests()
        self.assertEqual(len(received_input_files), 2)
        self.assertEqual(len(received_output_files), 2)
        # Assert they're sorted by name
        self.assertEqual(received_input_files, sorted(received_input_files, key=lambda x: x.name))
        self.assertEqual(received_output_files, sorted(received_output_files, key=lambda x: x.name))
        # Assert the appropriate functions were called
        scandir_mock.assert_called_once_with(TESTS_FOLDER_NAME)
        isdir_mock.assert_called_once_with(TESTS_FOLDER_NAME)

    @patch('challenges.grader.TESTS_FOLDER_NAME', 'InvA4$LiDaN$m')
    def test_find_tests_invalid_path_should_raise(self):
        expected_message = 'The path InvA4$LiDaN$m is invalid!'

        try:
            self.grader.find_tests()
            self.fail()
        except Exception as e:
            self.assertEqual(str(e), expected_message)

    @patch('challenges.grader.os.path.isdir')
    @patch('challenges.grader.os.scandir')
    def test_find_tests_invalid_file_count_should_raise(self, scandir_mock, isdir_mock):
        """ Given input/output file count that is not equal to the set count in the constructor, it should raise an exception """
        isdir_mock.return_value = True
        scandir_mock.return_value = self.input_files_dir_entries[2:]  # this should only give the grader 2 output files
        expected_error_message = 'Invalid input/output file count!'
        try:
            self.grader.find_tests()
            self.fail()
        except Exception as e:
            self.assertEqual(str(e), expected_error_message)

    def test_read_tests_invalid_file_count_should_raise(self):
        # It expects 2 input files and 2 output files, entering 3 and 2 should raise an error
        try:
            self.grader.read_tests(sorted_input_files=[MagicMock()] * 3, sorted_output_files=[MagicMock()] * 2)
            self.fail('Should have raised an exception')
        except Exception as e:
            self.assertEqual(str(e), (f'Input/Output files are not in pairs! \nInput:3\nOutput:2'))

    @patch('challenges.grader.open')
    @patch('os.path.abspath')
    def test_read_tests_invalid_file_name_should_raise(self, abspath_mock, open_mock):
        expected_error_message = 'Invalid input/output file names when reading them.'
        input_files, output_files = [DirEntryMock(name='OPSZSomeThinginput-01.txt', path='a'), DirEntryMock(name='input-02.txt', path='b')], [DirEntryMock(name='output-01.txt', path='c'), DirEntryMock(name='output-02.txt', path='d')]

        try:
            self.grader.read_tests(input_files, output_files)
            self.fail("Should have raised an exception")
        except Exception as e:
            self.assertEqual(str(e), expected_error_message)

    @patch('challenges.grader.open')
    @patch('os.path.abspath')
    def test_read_tests_work_correctly(self, abspath_mock, open_mock):
        abspath_mock.return_value = lambda x: x
        self.assertEqual(len(self.grader.test_cases), 0)  # the read_tests() method should fill the test_cases var
        self.assertFalse(self.grader.read_input)
        input_files, output_files = [DirEntryMock(name='input-01.txt', path='a'), DirEntryMock(name='input-02.txt', path='b')], [DirEntryMock(name='output-01.txt', path='c'), DirEntryMock(name='output-02.txt', path='d')]


        self.grader.read_tests(sorted_input_files=input_files, sorted_output_files=output_files)

        # assert the abspath and open was called with each of the files
        for ip_file in input_files:
            # open(os.path.abspath(input_file.path)) is the actual code
            abspath_mock.assert_any_call(ip_file.path)
            open_mock.assert_any_call(abspath_mock(ip_file.path))
        self.assertEqual(len(self.grader.test_cases), 2)
        self.assertTrue(all(isinstance(tc, GraderTestCase) for tc in self.grader.test_cases))
        self.assertTrue(self.grader.read_input)

    def test_cleanup_error_message(self):
        # It should return the same thing we passed it in the BaseGrader class
        self.assertEqual('100xar3353fva#FCA', self.grader.cleanup_error_message('100xar3353fva#FCA'))

    def test_run_program_process_should_raise_NotImplementedError(self):
        with self.assertRaises(NotImplementedError):
            self.grader.run_program_process()

    def test_grade_solution_should_raise_NotImplementedError(self):
        with self.assertRaises(NotImplementedError):
            self.grader.grade_solution()

    @patch('challenges.grader.BaseGrader.run_program_process')
    def test_test_solution_expected_output_should_grade_sucessfully(self, run_process_mock):
        self.grader.TIMEOUT_SECONDS = 10
        test_case = GraderTestCase(input_lines='', expected_output_lines=["1, 2, 3"])
        # Mock the process to return the expected outpu
        communicate_mock = MagicMock()
        communicate_mock.return_value = (b"1, 2, 3", b'')
        process_mock = MagicMock(communicate=communicate_mock)
        run_process_mock.return_value = process_mock

        result: dict = self.grader.test_solution(test_case)

        communicate_mock.assert_called_once_with(input=''.encode(), timeout=self.grader.TIMEOUT_SECONDS)
        self.assertTrue(result['success'], True)
        self.assertEqual(result['error_message'], '')
        self.assertEqual(result['traceback'], '')

    @patch('challenges.grader.BaseGrader.run_program_process')
    def test_test_solution_expected_output_multiple_lines_should_grade_sucessfully(self, run_process_mock):
        self.grader.TIMEOUT_SECONDS = 10
        test_case = GraderTestCase(input_lines='', expected_output_lines=["1", "2", "3"])
        # Mock the process to return the expected outpu
        process_mock = MagicMock(communicate=lambda input, timeout: (b"1\n2\n3", b''))
        run_process_mock.return_value = process_mock

        result: dict = self.grader.test_solution(test_case)

        self.assertTrue(result['success'], True)
        self.assertEqual(result['error_message'], '')
        self.assertEqual(result['traceback'], '')

    @patch('challenges.grader.BaseGrader.run_program_process')
    def test_test_solution_wrong_output_should_grade_as_failure(self, run_process_mock):
        self.grader.TIMEOUT_SECONDS = 10
        test_case = GraderTestCase(input_lines='', expected_output_lines=["1, 2, 3"])
        # Mock the process to return the expected outpu
        process_mock = MagicMock(communicate=lambda input, timeout: (b"1WROnG", b''))
        run_process_mock.return_value = process_mock

        result: dict = self.grader.test_solution(test_case)

        self.assertEqual(result['success'], False)
        self.assertIn('not equal', result['error_message'])

    @patch('challenges.grader.BaseGrader.cleanup_error_message')
    @patch('challenges.grader.BaseGrader.run_program_process')
    def test_test_solution_error_message_should_grade_as_failure(self, run_process_mock, error_cleanup_mock):
        error_msg = 'ERROR!'
        error_cleanup_mock.return_value = error_msg
        self.grader.TIMEOUT_SECONDS = 10
        test_case = GraderTestCase(input_lines='', expected_output_lines=["1, 2, 3"])
        # Mock the process to return the expected outpu
        process_mock = MagicMock(communicate=lambda input, timeout: (b"1, 2, 3", error_msg.encode('utf-8')))
        run_process_mock.return_value = process_mock

        result: dict = self.grader.test_solution(test_case)

        error_cleanup_mock.assert_called_once_with(error_msg)
        self.assertEqual(result['success'], False)
        self.assertEqual(result['traceback'], error_msg)
        self.assertEqual(result['error_message'], '')

    @patch('challenges.grader.BaseGrader.run_program_process')
    def test_test_solution_time_expire_should_grade_as_failure(self, run_process_mock):
        def raise_timeout_expired(*args, **kwargs):
            raise subprocess.TimeoutExpired('smth', 3)
        self.grader.TIMEOUT_SECONDS = 10
        test_case = GraderTestCase(input_lines='', expected_output_lines=["1, 2, 3"])
        # Mock the process to return the expected outpu

        kill_mock = Mock()
        communicate_mock = MagicMock()
        communicate_mock.side_effect = raise_timeout_expired  # make it raise the timeout err
        process_mock = MagicMock(communicate=communicate_mock, kill=kill_mock)
        run_process_mock.return_value = process_mock

        result: dict = self.grader.test_solution(test_case)

        kill_mock.assert_called_once()
        self.assertEqual(result['success'], False)
        self.assertEqual(result['traceback'], f'Timed out after {self.grader.TIMEOUT_SECONDS} seconds')
        self.assertEqual(result['error_message'], '')


class CompilableGraderTests(TestCase):
    def setUp(self):
        CompilableLangGrader.FILE_EXTENSION = 'woo'
        self.grader = CompilableLangGrader(5, 'whatup')
        self.grader.RUN_ARGS = []

    @patch('challenges.grader.CompilableLangGrader.find_tests')
    @patch('challenges.grader.CompilableLangGrader.read_tests')
    @patch('challenges.grader.CompilableLangGrader.compile')
    @patch('challenges.grader.CompilableLangGrader.grade_all_tests')
    def test_grade_solution_works_correctly(self, grade_all_tests_mock, compile_mock, read_tests_mock, find_tests_mock):
        """ The grade solution encompasses everything we want to do
            It should find the tests, read them, compile the solution code and call the grade_all_tests()
            if it compiled propely
        """
        expected_result = {'we aint ever getting older :)'}
        find_tests_mock.return_value = (1, 2)
        grade_all_tests_mock.return_value = expected_result
        self.grader.compiled = True

        received_result = self.grader.grade_solution()

        find_tests_mock.assert_called_once()
        read_tests_mock.assert_called_once_with(1, 2)  # the find_tests return values
        compile_mock.assert_called_once()
        grade_all_tests_mock.assert_called_once()
        self.assertEqual(received_result, expected_result)

    @patch('challenges.grader.CompilableLangGrader.find_tests')
    @patch('challenges.grader.CompilableLangGrader.read_tests')
    @patch('challenges.grader.CompilableLangGrader.compile')
    @patch('challenges.grader.CompilableLangGrader.grade_all_tests')
    def test_grade_solution_returns_compile_error_message_on_compile_failure(self, grade_all_tests_mock, compile_mock, read_tests_mock, find_tests_mock):
        """ The grade solution encompasses everything we want to do
            It should find the tests, read them, compile the solution code and call the grade_all_tests()
            if it compiled propely
        """
        compilation_err_msg = "Compilation failed because ...."
        expected_result = json.dumps({GRADER_COMPILE_FAILURE: compilation_err_msg})
        find_tests_mock.return_value = (1, 2)
        grade_all_tests_mock.return_value = compilation_err_msg
        self.grader.compiled = False
        self.grader.compile_error_message = compilation_err_msg  # compile() usually sets this

        received_result = self.grader.grade_solution()

        find_tests_mock.assert_called_once()
        read_tests_mock.assert_called_once_with(1, 2)  # the find_tests return values
        compile_mock.assert_called_once()
        grade_all_tests_mock.assert_not_called()

        self.assertEqual(received_result, expected_result)

    @patch('challenges.grader.SITE_ROOT', '/')
    @patch('challenges.grader.subprocess.PIPE', 'pipe')
    @patch('challenges.grader.CompilableLangGrader.has_compiled')
    @patch('challenges.grader.subprocess.Popen')
    def test_compile_works_correctly(self, popen_mock, has_compiled_mock):
        program_process = MagicMock()
        program_process.communicate.return_value = (b'aaa', b'')
        popen_mock.return_value = program_process
        has_compiled_mock.return_value = True
        self.grader.unique_name = 'woot'
        self.grader.temp_file_abs_path = './me.abv'
        self.grader.COMPILE_ARGS = ['some', 'args']
        expected_popen_args = ['some', 'args', './me.abv']
        expected_temp_exe_abs_path = '/woot'

        self.assertFalse(self.grader.compiled)
        self.assertIsNone(self.grader.temp_exe_abs_path)

        self.grader.compile()
        popen_mock.assert_called_once_with(expected_popen_args, stdout='pipe', stderr='pipe')
        has_compiled_mock.assert_called_once_with('')  # the empty error message
        self.assertTrue(self.grader.compiled)
        self.assertEqual(self.grader.temp_exe_abs_path, expected_temp_exe_abs_path)

    @patch('challenges.grader.CompilableLangGrader.has_compiled')
    @patch('challenges.grader.subprocess.Popen')
    def test_compile_marks_as_failed_when_error(self, popen_mock, has_compiled_mock):
        self.grader.COMPILE_ARGS = ['']
        program_process = MagicMock()
        program_process.communicate.return_value = (b'a', b'This is an error')
        popen_mock.return_value = program_process
        has_compiled_mock.return_value = False

        self.grader.compile()

        has_compiled_mock.assert_called_once_with('This is an error')
        self.assertFalse(self.grader.compiled)
        self.assertEqual(self.grader.compile_error_message, 'This is an error')

    @patch('challenges.grader.subprocess.PIPE', 'pipe')
    @patch('challenges.grader.subprocess.Popen')
    def test_run_program_process_works_correctly(self, popen_mock):
        """ Should open a process with the exe path and all stdouts pointing to subprocess.pipe"""
        self.grader.temp_exe_abs_path = '/exe/path.py'

        self.grader.run_program_process()

        popen_mock.assert_called_once_with(['/exe/path.py'], stdin='pipe', stdout='pipe', stderr='pipe')

    def test_has_compiled_works_correctly(self):
        """ Given an error message, this function should return true/false in accordance if the compile was successful"""
        self.assertFalse(self.grader.has_compiled('This is an error'))

    def test_has_compiled_empty_str(self):
        self.assertTrue(self.grader.has_compiled(''))


class InterpretableGraderTests(TestCase):
    def setUp(self):
        InterpretableLangGrader.FILE_EXTENSION = '.py'
        self.grader = InterpretableLangGrader(test_case_count=2, temp_file_name='temp_file')

    @patch('challenges.grader.InterpretableLangGrader.find_tests')
    @patch('challenges.grader.InterpretableLangGrader.read_tests')
    @patch('challenges.grader.InterpretableLangGrader.grade_all_tests')
    def test_grade_solution_works_correctly(self, grade_tests_mock, read_tests_mock, find_tests_mock):
        """ Should find the tests, read them and grade them all, returning the result"""
        find_tests_return_value = [1], [2]
        find_tests_mock.return_value = find_tests_return_value
        grade_tests_mock.return_value = "Expected"

        result = self.grader.grade_solution()

        read_tests_mock.assert_called_once_with(*find_tests_return_value)
        grade_tests_mock.assert_called_once()
        self.assertEqual(result, 'Expected')

    @patch('challenges.grader.subprocess.PIPE', 'pipe')
    @patch('challenges.grader.subprocess.Popen')
    def test_run_program_process_called_correctly(self, popen_mock):
        self.grader.RUN_COMMAND = 'better run better run '
        self.grader.temp_file_name = 'outrun my gun'
        expected_args = ['better run better run ', 'outrun my gun']

        self.grader.run_program_process()

        popen_mock.assert_called_once_with(expected_args, stdin='pipe', stdout='pipe', stderr='pipe')


class RustGraderTests(TestCase):
    def setUp(self):
        self.grader = RustGrader(3, 'a')

    def test_static_variables(self):
        from constants import RUSTLANG_TIMEOUT_SECONDS, RUSTLANG_FILE_EXTENSION, RUSTLANG_COMPILE_ARGS

        self.assertEqual(RustGrader.TIMEOUT_SECONDS, RUSTLANG_TIMEOUT_SECONDS)
        self.assertEqual(RustGrader.COMPILE_ARGS, RUSTLANG_COMPILE_ARGS)
        self.assertEqual(RustGrader.FILE_EXTENSION, RUSTLANG_FILE_EXTENSION)

    def test_has_compiled_empty_str_should_return_true(self):
        self.assertTrue(self.grader.has_compiled(''))

    def test_has_compiled_str_with_known_error_snippet(self):
        """ There are some constant messages that rust outputs as a warning and the program should ignore """
        from constants import RUSTLANG_ERROR_MESSAGE_SNIPPET
        self.assertFalse(self.grader.has_compiled(f'Afewifwajofjwaf{RUSTLANG_ERROR_MESSAGE_SNIPPET}fefaoifwjf'))

    def test_has_compiled_str_with_known_error_snippet2(self):
        """ There are some constant messages that rust outputs as a warning and the program should ignore """
        from constants import RUSTLANG_ERROR_MESSAGE_SNIPPET_2
        self.assertFalse(self.grader.has_compiled(f'Afewifwajofjwaf{RUSTLANG_ERROR_MESSAGE_SNIPPET_2}fefaoifwjf'))

    def test_has_compiled_warning(self):
        self.assertTrue(self.grader.has_compiled('Warning: The roof is on fire'))

    def test_cleanup_error_message_removes_unfriendly_message(self):
        from constants import RUSTLANG_UNFRIENDLY_ERROR_MESSAGE

        unfriendly_message = f'Me@{RUSTLANG_UNFRIENDLY_ERROR_MESSAGE}abv.bg'
        expected_message = 'Me@abv.bg'

        self.assertEqual(expected_message, self.grader.cleanup_error_message(unfriendly_message))

    def test_cleanup_error_message_doesnt_remove_error_message(self):
        from constants import RUSTLANG_ERROR_MESSAGE_SNIPPET, RUSTLANG_ERROR_MESSAGE_SNIPPET_2
        expected_message = f'Error here {RUSTLANG_ERROR_MESSAGE_SNIPPET} and {RUSTLANG_ERROR_MESSAGE_SNIPPET_2}re'

        self.assertEqual(expected_message, self.grader.cleanup_error_message(expected_message))


class CppGraderTests(TestCase):
    def setUp(self):
        self.temp_file_name = 'x'
        self.grader = CppGrader(3, self.temp_file_name)

    def test_static_variables(self):
        from constants import CPP_TIMEOUT_SECONDS, CPP_COMPILE_ARGS, CPP_FILE_EXTENSION
        self.assertEqual(self.grader.TIMEOUT_SECONDS, CPP_TIMEOUT_SECONDS)
        self.assertEqual(self.grader.COMPILE_ARGS, CPP_COMPILE_ARGS)
        self.assertEqual(self.grader.FILE_EXTENSION, CPP_FILE_EXTENSION)

    @patch('challenges.grader.SITE_ROOT', '/')
    @patch('challenges.grader.subprocess.PIPE', 'pipe')
    @patch('challenges.grader.CompilableLangGrader.has_compiled')
    @patch('challenges.grader.subprocess.Popen')
    def test_compile_works_correctly(self, popen_mock, has_compiled_mock):
        """ The compile here basically  has slightly  different compile args, namely,
        adding the absolute path to the desired executable"""
        program_process = MagicMock()
        program_process.communicate.return_value = (b'aaa', b'')
        popen_mock.return_value = program_process
        has_compiled_mock.return_value = True
        self.grader.unique_name = 'woot'
        self.grader.temp_file_abs_path = './me.abv'
        self.grader.COMPILE_ARGS = ['some', 'args']
        expected_popen_args = self.grader.COMPILE_ARGS + [self.grader.unique_name, f'/{self.grader.temp_file_name}']
        expected_temp_exe_abs_path = '/woot'

        self.assertFalse(self.grader.compiled)
        self.assertIsNone(self.grader.temp_exe_abs_path)

        self.grader.compile()

        popen_mock.assert_called_once_with(expected_popen_args, stdout='pipe', stderr='pipe')
        has_compiled_mock.assert_called_once_with('')  # the empty error message
        self.assertTrue(self.grader.compiled)
        self.assertEqual(self.grader.temp_exe_abs_path, expected_temp_exe_abs_path)


class PythonGraderTests(TestCase):
    def setUp(self):
        self.grader = PythonGrader(1, 'a')

    def test_static_variables(self):
        from constants import PYTHON_TIMEOUT_SECONDS, PYTHON_FILE_EXTENSION, PYTHON_RUN_COMMAND
        self.assertEqual(self.grader.TIMEOUT_SECONDS, PYTHON_TIMEOUT_SECONDS)
        self.assertEqual(self.grader.FILE_EXTENSION, PYTHON_FILE_EXTENSION)
        self.assertEqual(self.grader.RUN_COMMAND, PYTHON_RUN_COMMAND)


class KotlinGraderTests(TestCase):
    def setUp(self):
        self.temp_file_name = 'x'
        self.grader = KotlinGrader(3, self.temp_file_name)

    @patch('challenges.grader.subprocess.Popen')
    def test_run_program_process_attaches_jar_extension(self, popen_mock):
        self.grader.temp_exe_abs_path = 'tank'

        self.grader.run_program_process()

        self.assertEqual(self.grader.temp_exe_abs_path, 'tank.jar')

    @patch('challenges.grader.subprocess.Popen')
    def test_run_program_multiple_times_doesnt_attach_jar_always(self, popen_mock):
        self.grader.temp_exe_abs_path = 'tank'

        self.grader.run_program_process()
        self.grader.run_program_process()
        self.grader.run_program_process()
        self.grader.run_program_process()
        self.grader.run_program_process()

        self.assertEqual(self.grader.temp_exe_abs_path, 'tank.jar')
