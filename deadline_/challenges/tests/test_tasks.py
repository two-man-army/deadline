from unittest.mock import MagicMock, patch
from unittest import TestCase

from challenges.tests.helpers import get_mock_function_arguments
from challenges.tasks import run_grader_task, GRADER_COMPILE_FAILURE, GRADER_TEST_RESULTS_RESULTS_KEY, GRADER_TEST_RESULT_TIME_KEY
from challenges.tests.factories import SubmissionFactory
from accounts.tests.factories import UserFactory
from challenges.models import Proficiency


class TasksTests(TestCase):
    @patch('challenges.tasks.update_test_cases')
    @patch('challenges.tasks.grade_result')
    @patch('challenges.tasks.update_user_score')
    @patch('challenges.tasks.run_grader')
    def test_run_grader_task_updates_successful_solution(self, mock_run_grader, mock_update_user_score, mock_grade_result, mock_update_test_cases):
        """
        The run_grader_task should run the function that opens docker and runs the tests
        and update the submission with the given result
        :return:
        """
        mock_update_test_cases.return_value = 50  # should return the percentage of timed out test cases
        user = UserFactory()
        submission = SubmissionFactory(author=user)
        test_case_count = 5
        test_folder_name = '/tank/'
        code = 'print("hello world")'
        lang = "python3"
        submission_id = submission.id
        mock_run_grader.return_value = {GRADER_TEST_RESULTS_RESULTS_KEY: 'batman', GRADER_TEST_RESULT_TIME_KEY: 155}

        run_grader_task(test_case_count=test_case_count, test_folder_name=test_folder_name,
                        code=code, lang=lang, submission_id=submission_id)

        # since the run_grader has returned a submission that has compiled, we should update the test case objects,
        # the submission score and user score
        mock_run_grader.assert_called_once_with(test_case_count, test_folder_name, code, lang)
        mock_update_test_cases.assert_called()
        self.assertIn('batman', get_mock_function_arguments(mock_update_test_cases)) # grade results in the update_test_cases
        mock_grade_result.assert_called_once_with(submission, mock_update_test_cases.return_value, 155)
        mock_update_user_score.assert_called_once()
        update_us_arguments = get_mock_function_arguments(mock_update_user_score)
        self.assertIn(submission.author, update_us_arguments)
        self.assertIn(submission, update_us_arguments)

    @patch('challenges.tasks.run_grader')
    def test_run_grader_task_correctly_sets_on_compile_failure(self, mock_run_grader):
        Proficiency.objects.create(name='starter', needed_percentage=0)
        user = UserFactory()
        submission = SubmissionFactory(author=user)
        test_case_count = 5
        test_folder_name = '/tank/'
        code = 'print("hello world")'
        lang = "python3"
        submission_id = submission.id
        mock_run_grader.return_value = {GRADER_TEST_RESULTS_RESULTS_KEY: 'batman', GRADER_COMPILE_FAILURE: "FAILED MISERABLY"}

        run_grader_task(test_case_count=test_case_count, test_folder_name=test_folder_name,
                        code=code, lang=lang, submission_id=submission_id)

        # since we have a compile failure, the submission's compiled should be set to false
        submission.refresh_from_db()
        self.assertFalse(submission.compiled)
        self.assertFalse(submission.pending)
        self.assertEqual(submission.compile_error_message, "FAILED MISERABLY")