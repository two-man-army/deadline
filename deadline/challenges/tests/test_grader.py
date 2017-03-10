from django.test import TestCase
from challenges.grader import RustGrader, RustTestCase
from unittest.mock import MagicMock


class RustGraderTest(TestCase):
    def test_grader_should_not_compile(self):
        """ It should take a Challenge object and find its tests in the appropriate folder"""
        challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight.rs')
        challenge.name = 'three-six-eight'
        sol = MagicMock()
        sol.code = 'Run It, keep it one hunnid!'
        expected_error_message_part = "error: expected one of `!` or `::`, found `It`"
        rg = RustGrader(challenge, sol)
        self.assertTrue(rg.read_input)
        self.assertNotEqual(len(rg.test_cases), 0)
        self.assertIsInstance(rg.test_cases[0], RustTestCase)
        self.assertFalse(rg.compiled)
        self.assertFalse(sol.compiled)
        self.assertIn(expected_error_message_part, sol.compile_error_message)

    def test_grader_should_compile(self):
        """ It should take a Challenge object and find its tests in the appropriate folder"""
        challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight.rs')
        challenge.name = 'three-six-eight'
        sol = MagicMock()
        sol.code = 'fn main() {println!("{:?}", "go post");}'
        rg = RustGrader(challenge, sol)
        self.assertTrue(rg.read_input)
        self.assertNotEqual(len(rg.test_cases), 0)
        self.assertIsInstance(rg.test_cases[0], RustTestCase)
        self.assertTrue(rg.compiled)

    def test_grader_solution_should_pass(self):
        challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight.rs')
        challenge.name = 'three-six-eight'
        sol = MagicMock()
        sol.code = 'fn main() {println!("{}", "hello");}'
        rg = RustGrader(challenge, sol)
        results_dict = rg.test_solution(rg.test_cases[0])
        self.assertTrue(results_dict['success'])

