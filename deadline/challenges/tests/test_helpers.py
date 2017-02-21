import random
from django.test import TestCase
from challenges.models import Challenge, Submission, TestCase
from accounts.models import User
from challenges.helper import grade_result


class GradeResultTests(TestCase):
    """
    Test the grade_results function, which should update the submission's score in accordance to the passed tests
    """

    def setUp(self):
        self.user = User(email="hello@abv.bg", password='123', username='me')
        self.user.save()
        self.challenge = Challenge(name='Hello World!', description='Say hello',
                                   rating=10, score=100, test_file_name='smth',
                                   test_case_count=5)
        self.challenge.save()
        self.submission = Submission(challenge=self.challenge, author=self.user,
                                     code='hack you', task_id='123', result_score=0)
        self.submission.save()
        # create the test cases
        self.test_cases = []
        for _ in range(self.challenge.test_case_count):
            tst_case = TestCase(submission=self.submission, pending=False, success=random.choice[True, False])
            tst_case.save()
            self.test_cases.append(tst_case)

    def test_grade_result(self):
        num_successful_tests = len([True for test_case in self.test_cases if not test_case.pending and test_case.success])
        expected_score = self.challenge.score / num_successful_tests

        grade_result(submission=self.submission)

        # Should have updated the submission's score
        self.assertEqual(self.submission.result_score, expected_score)
