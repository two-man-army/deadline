import os

from django.db.models import Max

from constants import (
    GRADER_TEST_RESULT_TRACEBACK_KEY, GRADER_TEST_RESULTS_RESULTS_KEY, GRADER_TEST_RESULT_TIME_KEY,
    GRADER_TEST_RESULT_SUCCESS_KEY, GRADER_TEST_RESULT_ERROR_MESSAGE_KEY, GRADER_TEST_RESULT_DESCRIPTION_KEY)
from challenges.models import Challenge, Submission, TestCase
from accounts.models import User


def grade_result(submission: Submission):
    """ Given a tested submission, update it's score in accordance to the number of test cases passed"""
    challenge = submission.challenge  # type: Challenge

    num_successful_tests = len([True for ts_cs in submission.testcase_set.all()
                                if not ts_cs.pending and ts_cs.success])
    result_per_test = challenge.score / challenge.test_case_count

    submission.result_score = num_successful_tests * result_per_test
    submission.pending = False
    submission.save()


def update_user_score(user: User, submission: Submission) -> bool:
    """
    Given a tested submission with score, update the user's score IF:
        1. He has not submitted for the given challenge before
        2. He has submitted for the given challenge before but with a lower score
    Returns a boolean whether the score was updated or not
    """
    max_prev_score = Submission.objects.filter(challenge=submission.challenge, author=user) \
                                       .exclude(id=submission.id) \
                                       .all() \
                                       .aggregate(Max('result_score'))['result_score__max']

    if max_prev_score is None:
        # The user does not have any previous submissions, so we update his score
        user.score += submission.result_score
        user.save()
        return True
    elif max_prev_score < submission.result_score:
        # The user has submitted a better-scoring solution. Update his score
        score_improvement = submission.result_score - max_prev_score
        user.score += score_improvement
        user.save()
        return True

    return False


def update_test_cases(grader_results: dict, test_cases: [TestCase]):
    """
    Update every TestCase model with the information given by the grader
    :param grader_results: The results given by the grader
    :param test_cases: A list of TestCase objects
    :return:
    """
    for idx, test_case in enumerate(test_cases):
        test_results = grader_results[idx]
        test_case.success = test_results[GRADER_TEST_RESULT_SUCCESS_KEY]
        test_case.time = test_results[GRADER_TEST_RESULT_TIME_KEY] + 's'
        test_case.pending = False
        test_case.description = test_results[GRADER_TEST_RESULT_DESCRIPTION_KEY]
        test_case.traceback = test_results[GRADER_TEST_RESULT_TRACEBACK_KEY]
        test_case.error_message = test_results[GRADER_TEST_RESULT_ERROR_MESSAGE_KEY]
        test_case.save()  # TODO: Maybe save at once SOMEHOW, django transaction does not work


def convert_to_normal_text(lines: list) -> str:
    """ Given a list with byte strings with a new-line at the end, return a concatenated string """
    return ''.join([st.decode('utf-8') for st in lines])


def cleanup_rust_error_message(error_message: str) -> str:
    """ Removes unecessary information from a Rust error message, making it more user friendly"""
    unfriendly_emsg = "note: Run with `RUST_BACKTRACE=1`"  # it is always at the end

    if unfriendly_emsg in error_message:
        emsg_idx = error_message.index(unfriendly_emsg)
        error_message = error_message[:emsg_idx]

    return error_message


def delete_file(file_name):
    try:
        os.remove(file_name)
    except OSError:
        pass
