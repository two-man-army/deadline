from django.test import TestCase

from education.models import Course, Lesson, Homework, HomeworkTask, HomeworkTaskTest
from education.tests.factories import HomeworkTaskDescriptionFactory


class HomeworkTaskTestTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name='tank', difficulty=1, is_under_construction=False)
        self.lesson = Lesson.objects.create(lesson_number=1, course=self.course, intro='', content='',
                                            annexation='', is_under_construction=False)
        self.hw = Homework.objects.create(is_mandatory=False, lesson=self.lesson)
        self.hw_task = HomeworkTask.objects.create(test_case_count=1, description=HomeworkTaskDescriptionFactory(),
                                                   is_mandatory=True, consecutive_number=1, difficulty=10,
                                                   homework=self.hw)

    def test_creation(self):
        hw_t_test = HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye', task=self.hw_task)
        self.assertEqual(hw_t_test.consecutive_number, 1)
        # should not raise anything

    def test_ignores_consecutive_number(self):
        HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye',
                                        consecutive_number=1, task=self.hw_task)

        # there is already one test that is #1, as such we cannot put in another #1
        correct_number = 2
        task_test = HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye',
                                                    consecutive_number=1, task=self.hw_task)
        self.assertEqual(task_test.consecutive_number, correct_number)

    def test_post_save_consecutive_number_is_set_only_on_creation(self):
        task_test = HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye', task=self.hw_task)
        self.assertEqual(task_test.consecutive_number, 1)
        HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye', task=self.hw_task)
        HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye', task=self.hw_task)
        task_test.input_file_path = 'tank'
        task_test.save()
        self.assertEqual(task_test.consecutive_number, 1)

    def test_creation_increments_task_test_case_count(self):
        old_tc_count = self.hw_task.test_case_count
        task_test = HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye',
                                                    consecutive_number=1, task=self.hw_task)
        self.hw_task.refresh_from_db()

        self.assertEqual(self.hw_task.test_case_count, old_tc_count + 1)

    def test_save_hook_does_not_increment_test_case_count(self):
        task_test = HomeworkTaskTest.objects.create(input_file_path='hello', output_file_path='bye',
                                                    consecutive_number=1, task=self.hw_task)
        self.hw_task.refresh_from_db()
        old_tc_count = self.hw_task.test_case_count
        task_test.output_file_path = 'tank'
        task_test.save()
        self.hw_task.refresh_from_db()

        self.assertEqual(old_tc_count, self.hw_task.test_case_count)
