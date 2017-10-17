import random
from unittest.mock import patch

from django.test import TestCase

from challenges.models import (
    Challenge, Submission, TestCase as TestCaseModel, MainCategory, SubCategory, ChallengeDescription,
    Language, UserSubcategoryProficiency, Proficiency, SubcategoryProficiencyAward, UserSolvedChallenges)

from accounts.models import User
from challenges.helper import grade_result, update_user_score, update_user_info
from challenges.tests.factories import ChallengeDescFactory
from challenges.tests.base import TestHelperMixin


class GradeResultTests(TestCase, TestHelperMixin):
    """
    Test the grade_results function, which should update the submission's score in accordance to the passed tests
    """

    def setUp(self):
        self.base_set_up()
        # create the test cases
        self.test_cases = []
        for _ in range(self.challenge.test_case_count):
            tst_case = TestCaseModel(submission=self.submission, pending=False, success=random.choice([True, False]))
            tst_case.save()
            self.test_cases.append(tst_case)

    def test_grade_result(self):
        num_successful_tests = len([True for test_case in self.test_cases if not test_case.pending and test_case.success])
        expected_score =  num_successful_tests * (self.challenge.score / self.challenge.test_case_count)

        grade_result(submission=self.submission, timed_out_percentage=0, elapsed_seconds=1.1)

        # Should have updated the submission's score
        self.assertEqual(self.submission.result_score, expected_score)
        self.assertFalse(self.submission.timed_out)
        self.assertEqual(self.submission.elapsed_seconds, 1.1)

    def test_grade_result_should_set_timed_out_var_and_elapsed_seconds(self):
        from constants import SUBMISSION_MINIMUM_TIMED_OUT_PERCENTAGE
        grade_result(submission=self.submission, timed_out_percentage=SUBMISSION_MINIMUM_TIMED_OUT_PERCENTAGE, elapsed_seconds=1.1)
        self.assertTrue(self.submission.timed_out)
        self.assertEqual(self.submission.elapsed_seconds, 1.1)


@patch('challenges.helper.update_user_score')
class UpdateUserInfoTests(TestCase, TestHelperMixin):
    """
    The update_user_info function should create a UserSolvedChallenges object if such doesnt exist
        and call update_user_score
    """
    def setUp(self):
        self.base_set_up()
        self.submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                    author=self.auth_user, code="", result_score=self.challenge.score)

    def test_creates_solved_challenges_record_when_challenge_fully_solved(self, mock_update_user_score):
        update_user_info(submission=self.submission)

        self.assertEqual(UserSolvedChallenges.objects.count(), 1)
        usc = UserSolvedChallenges.objects.first()
        self.assertEqual(usc.user, self.submission.author)
        self.assertEqual(usc.challenge, self.submission.challenge)
        mock_update_user_score.assert_called_once()

    def test_doesnt_create_solved_challenges_record_when_challenge_not_fully_solved(self, mock_update_user_score):
        self.submission.result_score -= 1
        self.submission.save()

        update_user_info(submission=self.submission)

        self.assertEqual(UserSolvedChallenges.objects.count(), 0)
        mock_update_user_score.assert_called_once()

    def test_doesnt_create_solved_challenges_record_when_record_exists(self, mock_update_user_score):
        UserSolvedChallenges.objects.create(user=self.submission.author, challenge=self.submission.challenge)
        self.assertEqual(UserSolvedChallenges.objects.count(), 1)

        update_user_info(submission=self.submission)

        self.assertEqual(UserSolvedChallenges.objects.count(), 1)
        mock_update_user_score.assert_called_once()


class UpdateUserScoreTests(TestCase, TestHelperMixin):
    """
    the update_user_score function should update the user's overall score given a submission by him.
    It should also update the UserSubcategoryProgress model associated to it
    Note: It should only update it if the user has a previous submission (or none at all) which has a lower score.
    """
    def setUp(self):
        self.base_set_up()
        self.submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                    author=self.auth_user, code="", result_score=20)
        self.subcategory_progress.user_score = 20
        self.subcategory_progress.save()
        # add this submisssions score to him
        self.auth_user = self.auth_user
        self.auth_user.score = 20
        self.auth_user.save()

    def test_submission_with_lower_score_should_not_update(self):
        lower_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                     code='hack you', task_id='123', result_score=10)
        # subcategory_progress should not update either
        old_sc_progress = self.subcategory_progress.user_score

        result = update_user_score(user=self.auth_user, submission=lower_submission)

        self.subcategory_progress.refresh_from_db()
        self.assertEqual(self.subcategory_progress.user_score, old_sc_progress)
        self.assertFalse(result)
        self.auth_user.refresh_from_db()
        self.assertEqual(self.auth_user.score, 20)  # should not have changed

    def test_submission_with_higher_score_should_update_proficiency_score_and_user_score(self):
        higher_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                                     code='hack you', task_id='123', result_score=30)
        old_sc_progress = self.subcategory_progress.user_score

        result = update_user_score(user=self.auth_user, submission=higher_submission)

        self.subcategory_progress.refresh_from_db()
        # should have updated subcategory_progress as well
        self.assertNotEqual(self.subcategory_progress.user_score, old_sc_progress)
        self.assertEqual(self.subcategory_progress.user_score, 30)
        self.assertTrue(result)
        self.auth_user.refresh_from_db()
        self.assertEqual(self.auth_user.score, 30)  # should have changed

    def test_submission_new_challenge_should_update(self):
        """ Since the user does not have a submission for this challenge, it should update his score """
        sample_desc2 = ChallengeDescFactory()
        new_challenge = Challenge.objects.create(name='NEW MAN', description=sample_desc2,
                                                 difficulty=10, score=100, test_file_name='smth',
                                                 test_case_count=3, category=self.sub_cat)
        new_submission = Submission.objects.create(language=self.python_language, challenge=new_challenge, author=self.auth_user,
                                                   code='hack you', task_id='123', result_score=100)
        old_sc_progress = self.subcategory_progress.user_score

        result = update_user_score(user=self.auth_user, submission=new_submission)

        # should also update his subcategory_progress by 100
        self.subcategory_progress.refresh_from_db()
        self.assertEqual(self.subcategory_progress.user_score, old_sc_progress + 100)
        self.assertTrue(result)
        self.auth_user.refresh_from_db()
        self.assertEqual(self.auth_user.score, 120)  # should have updated it

    def test_submission_jumping_to_new_proficiency_should_reach_it(self):
        next_prof = Proficiency.objects.create(name='mid', needed_percentage=10)
        SubcategoryProficiencyAward.objects.create(subcategory=self.sub_cat, proficiency=next_prof, xp_reward=1000)
        higher_submission = Submission.objects.create(language=self.python_language, challenge=self.challenge, author=self.auth_user,
                                                      code='hack you', task_id='123', result_score=30)
        expected_user_score = 1000 + 30  # proficiency award + submission
        expected_prof = next_prof

        update_user_score(user=self.auth_user, submission=higher_submission)

        self.subcategory_progress.refresh_from_db()
        self.auth_user.refresh_from_db()
        self.assertEqual(expected_user_score, self.auth_user.score)
        self.assertEqual(self.subcategory_progress.proficiency, expected_prof)
