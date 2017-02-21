from challenges.models import Challenge, Submission, TestCase


def grade_result(submission: Submission):
    """ Given a tested submission, update it's score in accordance to the number of test cases passed"""
    challenge = submission.challenge  # type: Challenge

    num_successful_tests = len([True for test_case in submission.testcase_set.all()
                                if not test_case.pending and test_case.success])

    submission.result_score = challenge.score / num_successful_tests
    submission.save()
