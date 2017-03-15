from django.test import TestCase
from challenges.grader import RustGrader, RustTestCase
from unittest.mock import MagicMock

# TODO: Test will need rework after the timing of the test is functional, since the hardcoded expected JSONs
# have "time": "0s" in it and there will be no way to know the amount of time it'll take to run the program
class RustGraderTest(TestCase):
    def test_grader_should_not_compile(self):
        """ It should take a Challenge object and find its tests in the appropriate folder"""
        challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
        challenge.name = 'three-six-eight'
        sol = MagicMock()
        sol.code = 'Run It, keep it one hunnid!'
        expected_error_message_part = "error: expected one of `!` or `::`, found `It`"
        rg = RustGrader(challenge, sol)
        rg.run_solution()
        self.assertTrue(rg.read_input)
        self.assertNotEqual(len(rg.test_cases), 0)
        self.assertIsInstance(rg.test_cases[0], RustTestCase)
        self.assertFalse(rg.compiled)
        self.assertFalse(sol.compiled)
        self.assertIn(expected_error_message_part, sol.compile_error_message)

    def test_grader_should_compile(self):
        """ It should take a Challenge object and find its tests in the appropriate folder"""
        challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
        challenge.name = 'three-six-eight'
        sol = MagicMock()
        sol.code = 'fn main() {println!("{:?}", "go post");}'
        rg = RustGrader(challenge, sol)
        rg.run_solution()

        self.assertTrue(rg.read_input)
        self.assertNotEqual(len(rg.test_cases), 0)
        self.assertIsInstance(rg.test_cases[0], RustTestCase)
        self.assertTrue(rg.compiled)

    def test_grader_solution_should_pass(self):
        challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
        challenge.name = 'three-six-eight'
        sol = MagicMock()
        sol.code = 'fn main() {println!("{}", "hello");}'

        rg = RustGrader(challenge, sol)

        json_result = rg.run_solution()
        self.assertIn('success', json_result)

    def test_grader_grade_all_solutions(self):
        challenge = MagicMock(test_case_count=1, test_file_name='three-six-eight')
        challenge.name = 'three-six-eight'
        expected_json = '{"results": [{"error_message": "", "success": true, "time": "0s"}]}'
        sol = MagicMock()
        sol.code = 'fn main() {println!("{}", "hello");}'
        rg = RustGrader(challenge, sol)
        json_result = rg.run_solution()

        self.assertEqual(json_result, expected_json)

    def test_grader_sum_array(self):
        challenge = MagicMock(test_case_count=5, test_file_name='array_sum_tests')
        challenge.name = 'Sum Array'
        sol = MagicMock()
        sol.code = """use std::io;

fn main(){
    let mut input = String::new();
    let stdin = std::io::stdin();
    stdin.read_line(&mut input);
    let numbers: Vec<f64> = input.trim().split(", ").map(|x| x.parse::<f64>().unwrap()).collect();
    let sum: f64 = numbers.iter().sum();
    println!("{}", sum);
}
"""
        expected_json = '{"results": [{"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}, {"error_message": "", "success": true, "time": "0s"}]}'
        rg = RustGrader(challenge, sol)

        self.assertEqual(rg.run_solution(), expected_json)

    def test_grader_sum_array_incorrect(self):
        challenge = MagicMock(test_case_count=5, test_file_name='array_sum_tests')
        challenge.name = 'Sum Array'
        sol = MagicMock()
        sol.code = """use std::io;

        fn main(){
            let mut input = String::new();
            let stdin = std::io::stdin();
            stdin.read_line(&mut input);
            let numbers: Vec<f64> = input.trim().split(", ").map(|x| x.parse::<f64>().unwrap()).collect();
            let sum: f64 = numbers.iter().sum();
            println!("{}", sum+1.0);
        }

        """
        expected_json = '{"results": [{"error_message": "16 is not equal to the expected 15", "success": false, "time": "0s"}, {"error_message": "91 is not equal to the expected 90", "success": false, "time": "0s"}, {"error_message": "34 is not equal to the expected 33", "success": false, "time": "0s"}, {"error_message": "1 is not equal to the expected 0", "success": false, "time": "0s"}, {"error_message": "4594850 is not equal to the expected 4594849", "success": false, "time": "0s"}]}'
        rg = RustGrader(challenge, sol)
        self.assertEqual(rg.run_solution(), expected_json)
