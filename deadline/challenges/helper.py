from django.db.models import Max
from challenges.models import Challenge, Submission, TestCase
from accounts.models import User

def grade_result(submission: Submission):
    """ Given a tested submission, update it's score in accordance to the number of test cases passed"""
    challenge = submission.challenge  # type: Challenge

    num_successful_tests = len([True for test_case in submission.testcase_set.all()
                                if not test_case.pending and test_case.success])

    submission.result_score = challenge.score / num_successful_tests
    submission.save()


def update_user_score(user: User, submission: Submission) -> bool:
    """
    Given a tested submission with score, update the user's score IF:
        1. He has not submitted for the given challenge before
        2. He has submitted for the given challenge before but with a lower score
    Returns a boolean whether the score was updated or not
    """
    prev_submission = Submission.objects.filter(challenge=submission.challenge, author=user).all().aggregate(Max('result_score'))
    if prev_submission is not None and prev_submission.result_score < submission.result_score:
        # The user has submitted a better-scoring solution. Update his score
        score_improvement = submission.result_score - prev_submission.result_score
        user.score += score_improvement
        user.save()
        return True
    elif prev_submission is None:
        # The user does not have any previous submissions, so we update his score
        user.score += submission.result_score
        user.save()
        return True

    return False

