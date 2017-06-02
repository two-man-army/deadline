import random
from django.test import TestCase
from challenges.models import (
    Challenge, Submission, TestCase as TestCaseModel, MainCategory, SubCategory, ChallengeDescription,
    Language, UserSubcategoryProgress, Proficiency)

from accounts.models import User
from challenges.helper import grade_result, update_user_score


class GradeResultTests(TestCase):
    """
    Test the grade_results function, which should update the submission's score in accordance to the passed tests
    """

    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.python_language = Language.objects.create(name="Python")
        self.sample_desc.save()
        challenge_cat = MainCategory.objects.create(name='Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.user = User(email="hello@abv.bg", password='123', username='me')
        self.user.save()
        self.challenge = Challenge(name='Hello World!', description=self.sample_desc,
                                   difficulty=10, score=100, test_file_name='smth',
                                   test_case_count=5, category=self.sub_cat)
        self.challenge.save()
        self.submission = Submission(language=self.python_language, challenge=self.challenge, author=self.user,
                                     code='hack you', task_id='123', result_score=0)
        self.submission.save()
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


class UpdateUserScoreTests(TestCase):
    """
    the update_user_score function should update the user's overall score given a submission by him.
    It should also update the UserSubcategoryProgress model associated to it
    Note: It should only update it if the user has a previous submission (or none at all) which has a lower score.
    """
    def setUp(self):
        self.sample_desc = ChallengeDescription(content='What Up', input_format='Something',
                                                output_format='something', constraints='some',
                                                sample_input='input sample', sample_output='output sample',
                                                explanation='gotta push it to the limit')
        self.python_language = Language.objects.create(name="Python")
        self.sample_desc.save()
        challenge_cat = MainCategory.objects.create(name='Tests')
        challenge_cat.save()
        self.sub_cat = SubCategory(name='tests', meta_category=challenge_cat)
        self.sub_cat.save()
        Proficiency.objects.create(name='starter', needed_percentage=0)
        self.user = User(email="hello@abv.bg", password='123', username='me')
        self.user.save()

        self.subcategory_progress = UserSubcategoryProgress.objects.filter(subcategory=self.sub_cat, user=self.user).first()
        self.challenge = Challenge(name='Hello World!', description=self.sample_desc,
                                   difficulty=10, score=100, test_file_name='smth',
                                   test_case_count=3, category=self.sub_cat)
        self.challenge.save()
        self.submission = Submission(language=self.python_language, challenge=self.challenge, author=self.user,
                                     code='hack you', task_id='123', result_score=20)
        self.submission.save()
        self.subcategory_progress.user_score = 20
        self.subcategory_progress.save()
        # add this submisssions score to him
        self.user.score = 20
        self.user.save()

    def test_submission_with_lower_score_should_not_update(self):
        lower_submission = Submission(language=self.python_language, challenge=self.challenge, author=self.user,
                                     code='hack you', task_id='123', result_score=10)
        lower_submission.save()
        # subcategory_rprogress should not update either
        old_sc_progress = self.subcategory_progress.user_score

        result = update_user_score(user=self.user, submission=lower_submission)

        self.subcategory_progress.refresh_from_db()
        self.assertEqual(self.subcategory_progress.user_score, old_sc_progress)
        self.assertFalse(result)
        self.user.refresh_from_db()
        self.assertEqual(self.user.score, 20)  # should not have changed

    def test_submission_with_higher_score_should_update(self):
        higher_submission = Submission(language=self.python_language, challenge=self.challenge, author=self.user,
                                       code='hack you', task_id='123', result_score=30)
        higher_submission.save()
        old_sc_progress = self.subcategory_progress.user_score

        result = update_user_score(user=self.user, submission=higher_submission)

        self.subcategory_progress.refresh_from_db()
        # should have updated subcategory_progress as well
        self.assertNotEqual(self.subcategory_progress.user_score, old_sc_progress)
        self.assertEqual(self.subcategory_progress.user_score, 30)
        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertEqual(self.user.score, 30)  # should have changed

    def test_submission_new_challenge_should_update(self):
        """ Since the user does not have a submission for this challenge, it should update his score """
        sample_desc2 = ChallengeDescription(2, 'What Up', 'Ws', 's', 'some', 'input sample', 'output sample', 'gg')
        sample_desc2.save()
        new_challenge = Challenge(name='NEW MAN', description=sample_desc2,
                                   difficulty=10, score=100, test_file_name='smth',
                                   test_case_count=3, category=self.sub_cat)
        new_challenge.save()
        new_submission = Submission(language=self.python_language, challenge=new_challenge, author=self.user,
                                    code='hack you', task_id='123', result_score=100)
        new_submission.save()
        old_sc_progress = self.subcategory_progress.user_score

        result = update_user_score(user=self.user, submission=new_submission)

        # should also update his subcategory_progress by 100
        self.subcategory_progress.refresh_from_db()
        self.assertEqual(self.subcategory_progress.user_score, old_sc_progress + 100)
        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertEqual(self.user.score, 120)  # should have updated it
