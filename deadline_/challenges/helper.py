import os

from django.db.models import Max

from constants import (
    GRADER_TEST_RESULT_TRACEBACK_KEY, GRADER_TEST_RESULTS_RESULTS_KEY, GRADER_TEST_RESULT_TIME_KEY,
    GRADER_TEST_RESULT_SUCCESS_KEY, GRADER_TEST_RESULT_ERROR_MESSAGE_KEY, GRADER_TEST_RESULT_DESCRIPTION_KEY,
    GRADER_TEST_RESULT_TIMED_OUT_KEY, SUBMISSION_MINIMUM_TIMED_OUT_PERCENTAGE)
from challenges.models import Challenge, Submission, TestCase, UserSubcategoryProficiency, UserSolvedChallenges
from accounts.models import User


def grade_result(submission: Submission, timed_out_percentage: int, elapsed_seconds: float):
    """
    Given a tested submission and the percentage of test cases that have timed out,
        update its score in accordance to the number of test cases passed
        and if more than 40% of the test cases have timed out, set the Submission's timed_out field as true
    """
    challenge: Challenge = submission.challenge

    num_successful_tests = len([True for ts_cs in submission.testcase_set.all()
                                if not ts_cs.pending and ts_cs.success])
    result_per_test = challenge.score / challenge.test_case_count

    submission.result_score = num_successful_tests * result_per_test
    submission.pending = False
    submission.elapsed_seconds = elapsed_seconds
    if timed_out_percentage >= SUBMISSION_MINIMUM_TIMED_OUT_PERCENTAGE:
        submission.timed_out = True
    submission.save()


def update_user_info(submission: Submission):
    """
    Updates information related to the Submission's author
    """
    if (submission.result_score == submission.challenge.score
            and not UserSolvedChallenges.objects.filter(user=submission.author, challenge=submission.challenge).exists()):
        # Create a UserSolvedChallenge record
        UserSolvedChallenges.objects.create(user=submission.author, challenge=submission.challenge)
    update_user_score(user=submission.author, submission=submission)


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

    if max_prev_score is None or max_prev_score < submission.result_score:
        score_improvement = None
        if max_prev_score is None:
            # The user does not have any previous submissions, so we update his score
            score_improvement = submission.result_score
        else:
            # The user has submitted a better-scoring solution. Update his score
            score_improvement = submission.result_score - max_prev_score

        user_subcat_progress: UserSubcategoryProficiency = user.fetch_subcategory_proficiency(submission.challenge.category_id)
        user_subcat_progress.user_score += score_improvement
        user_subcat_progress.save()

        user.score += score_improvement
        user.save()

        # try to update the user's proficiency
        updated_proficiency = user_subcat_progress.try_update_proficiency()
        return True

    return False


def update_test_cases(grader_results: dict, test_cases: [TestCase]) -> int:
    """
    Update every TestCase model with the information given by the grader
    :param grader_results: The results given by the grader
    :param test_cases: A list of TestCase objects
    :return: a percentage of the overall timed out test cases
        i.e 5 out of 10 test cases timed out, -> 0.5
    """
    timed_out_count = 0
    for idx, test_case in enumerate(test_cases):
        test_results = grader_results[idx]
        test_case.success = test_results[GRADER_TEST_RESULT_SUCCESS_KEY]
        test_case.time = test_results[GRADER_TEST_RESULT_TIME_KEY]
        test_case.timed_out = test_results[GRADER_TEST_RESULT_TIMED_OUT_KEY]
        timed_out_count += int(test_case.timed_out)
        test_case.pending = False
        test_case.description = test_results[GRADER_TEST_RESULT_DESCRIPTION_KEY]
        test_case.traceback = test_results[GRADER_TEST_RESULT_TRACEBACK_KEY]
        test_case.error_message = test_results[GRADER_TEST_RESULT_ERROR_MESSAGE_KEY]
        test_case.save()  # TODO: Maybe save at once SOMEHOW, django transaction does not work
    timed_out_percentage = int((timed_out_count / len(test_cases)) * 100)
    return timed_out_percentage


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
