import json
from unittest.mock import MagicMock, Mock, patch, mock_open
import subprocess

from django.test import TestCase

from constants import TESTS_FOLDER_NAME
from challenges.grader import RustGrader, GraderTestCase, BaseGrader


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
        # MagicMock.__gt__ = lambda x, y: x.name > y.name
        self.input_files_dir_entries = [DirEntryMock(name='input-01.txt'), DirEntryMock(name='input-02.txt'),
                                        DirEntryMock(name='output-01.txt'), DirEntryMock(name='output-02.txt')]

    @patch('challenges.grader.BaseGrader.test_solution')
    def test_grade_all_tests(self, mocked_test_solution):
        """ Method should go through every input/output and run self.test_solution() for it """
        mocked_test_solution.return_value = 42
        self.grader.test_cases = [None] * 10  # 10 empty items

        expected_result = {'results': [42] * 10}  # should basically call test_solution 10 times
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

# TODO: Test will need rework after the timing of the test is functional, since the hardcoded expected JSONs
# have "time": "0s" in it and there will be no way to know the amount of time it'll take to run the program
# class RustGraderTest(TestCase):
#     def test_grader_should_not_compile(self):
#         """ It should take a Challenge object and find its tests in the appropriate folder"""
#         challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
#         challenge.name = 'three-six-eight'
#         sol = MagicMock()
#         sol.code = 'Run It, keep it one hunnid!'
#         expected_error_message_part = "error: expected one of `!` or `::`, found `It`"
#         rg = RustGrader(challenge, sol)
#         rg.run_solution()
#         self.assertTrue(rg.read_input)
#         self.assertNotEqual(len(rg.test_cases), 0)
#         self.assertIsInstance(rg.test_cases[0], GraderTestCase)
#         self.assertFalse(rg.compiled)
#         self.assertFalse(sol.compiled)
#         self.assertIn(expected_error_message_part, sol.compile_error_message)
#
#     def test_grader_should_compile(self):
#         """ It should take a Challenge object and find its tests in the appropriate folder"""
#         challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
#         challenge.name = 'three-six-eight'
#         sol = MagicMock()
#         sol.code = 'fn main() {println!("{:?}", "go post");}'
#         rg = RustGrader(challenge, sol)
#         rg.run_solution()
#
#         self.assertTrue(rg.read_input)
#         self.assertNotEqual(len(rg.test_cases), 0)
#         self.assertIsInstance(rg.test_cases[0], GraderTestCase)
#         self.assertTrue(rg.compiled)
#
#     def test_grader_solution_should_pass(self):
#         challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
#         challenge.name = 'three-six-eight'
#         sol = MagicMock()
#         sol.code = 'fn main() {println!("{}", "hello");}'
#
#         rg = RustGrader(challenge, sol)
#
#         json_result = rg.run_solution()
#         self.assertIn('success', json_result)
#
#     def test_grader_grade_all_solutions(self):
#         challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
#         challenge.name = 'three-six-eight'
#         expected_json = '{"results": [{"error_message": "", "success": true, "time": "0s"}]}'
#         sol = MagicMock()
#         sol.code = 'fn main() {println!("{}", "hello");}'
#         rg = RustGrader(challenge, sol)
#         json_result = rg.run_solution()
#
#         self.assertEqual(json_result, expected_json)
#
#     def test_grader_sum_array(self):
#         challenge = MagicMock(test_case_count=5, test_file_name='array_sum_tests')
#         challenge.name = 'Sum Array'
#         sol = MagicMock()
#         sol.code = """use std::io;
#
# fn main(){
#     let mut input = String::new();
#     let stdin = std::io::stdin();
#     stdin.read_line(&mut input);
#     let numbers: Vec<f64> = input.trim().split(", ").map(|x| x.parse::<f64>().unwrap()).collect();
#     let sum: f64 = numbers.iter().sum();
#     println!("{}", sum);
# }
# """
#         expected_json = '{"results": [{"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}]}'
#         rg = RustGrader(challenge, sol)
#
#         self.assertEqual(rg.run_solution(), expected_json)
#
#     def test_grader_sum_array_incorrect(self):
#         challenge = MagicMock(test_case_count=5, test_file_name='array_sum_tests')
#         challenge.name = 'Sum Array'
#         sol = MagicMock()
#         sol.code = """use std::io;
#
#         fn main(){
#             let mut input = String::new();
#             let stdin = std::io::stdin();
#             stdin.read_line(&mut input);
#             let numbers: Vec<f64> = input.trim().split(", ").map(|x| x.parse::<f64>().unwrap()).collect();
#             let sum: f64 = numbers.iter().sum();
#             println!("{}", sum+1.0);
#         }
#
#         """
#         expected_json = '{"results": [{"error_message": "16 is not equal to the expected 15", "success": false, "time": "0s"}, {"error_message": "91 is not equal to the expected 90", "success": false, "time": "0s"}, {"error_message": "34 is not equal to the expected 33", "success": false, "time": "0s"}, {"error_message": "1 is not equal to the expected 0", "success": false, "time": "0s"}, {"error_message": "4594850 is not equal to the expected 4594849", "success": false, "time": "0s"}]}'
#         rg = RustGrader(challenge, sol)
#         self.assertEqual(rg.run_solution(), expected_json)
