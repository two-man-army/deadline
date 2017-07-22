from unittest.mock import patch

from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from challenges.models import Language
from education.tests.factories import HomeworkTaskDescriptionFactory
from education.models import Course, Lesson, Homework, HomeworkTask, HomeworkTaskTest


@patch('education.views.homework_views.create_task_test_files')
class HomeworkTaskCreateViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.python_language = Language.objects.create(name='Python')
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are you', annexation='bye',
                                            course=self.course)
        self.hw = Homework.objects.create(lesson=self.lesson, is_mandatory=True)
        self.task = HomeworkTask.objects.create(
            homework=self.hw, test_case_count=0, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=1, difficulty=5)
        self.input = """1
2 3 0
1 2 0
        """
        self.output = """0
3
        """

    def test_create_normal_test(self, mock_create_task):
        mock_create_task.return_value = ('input_path/', 'output_path/')
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})
        self.task.refresh_from_db()
        task_test: HomeworkTaskTest = HomeworkTaskTest.objects.first()

        mock_create_task.assert_called_once_with(task_tests_dir=self.task.get_absolute_test_files_path(), test_number=self.task.test_case_count,
                                                 input=self.input, output=self.output)
        self.assertEqual(task_test.input_file_path, 'input_path/')
        self.assertEqual(task_test.output_file_path, 'output_path/')
        self.assertEqual(task_test.consecutive_number, 1)
        self.assertEqual(resp.status_code, 201)
        self.task.refresh_from_db()
        self.assertEqual(self.task.test_case_count, 1)


    def test_create_test_fails_for_non_teacher(self, _):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)

    def test_create_test_fails_for_teacher_that_is_not_part_of_course(self, _):
        self.create_teacher_user_and_auth_token()
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.second_teacher_auth_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(HomeworkTaskTest.objects.count(), 0)

    def test_create_test_fails_homework_task_that_is_not_under_construction(self, _):
        self.task.is_under_construction = False
        self.task.save()

        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)

    def test_create_test_fails_for_non_existent_course(self, _):
        resp = self.client.post(f'/education/course/12/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})
        self.assertEqual(resp.status_code, 404)

    def test_create_test_fails_for_non_existent_lesson(self, _):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/15/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})
        self.assertEqual(resp.status_code, 404)

    def test_create_test_fails_for_non_existent_task(self, _):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/15/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})
        self.assertEqual(resp.status_code, 404)

    def test_create_test_fails_for_lesson_that_is_not_part_of_course(self, _):
        # create a new course/lesson/hw/task
        course_two = Course.objects.create(name='teste fundamentals II', difficulty=1,
                                           is_under_construction=True, main_teacher=self.teacher_auth_user)
        lesson_two = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are you', annexation='bye',
                                            course=course_two)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{lesson_two.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)

    def test_create_test_fails_for_task_that_is_not_part_of_lesson(self, _):
        # create a new course/lesson/hw/task
        course_two = Course.objects.create(name='teste fundamentals II', difficulty=1,
                                           is_under_construction=True, main_teacher=self.teacher_auth_user)
        lesson_two = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                           intro='hello', content='how are you', annexation='bye',
                                           course=course_two)
        hw_two = Homework.objects.create(lesson=lesson_two, is_mandatory=True)
        task_two = HomeworkTask.objects.create(
            homework=hw_two, test_case_count=0, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=1, difficulty=5)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{task_two.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)


class LessonHomeworkTaskDeleteViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.python_language = Language.objects.create(name='Python')
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are you', annexation='bye',
                                            course=self.course)
        self.hw = Homework.objects.create(lesson=self.lesson, is_mandatory=True)
        self.task = HomeworkTask.objects.create(
            homework=self.hw, test_case_count=0, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=1, difficulty=5)

    def test_delete_task(self):
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 204)
        self.task.refresh_from_db()
        # assert its not deleted
        self.assertEqual(HomeworkTask.objects.count(), 1)
        self.assertNotEqual(self.task.homework_id, self.hw.id)

    def test_delete_re_orders_consecutive_number(self):
        second_task = HomeworkTask.objects.create(
            homework=self.hw, test_case_count=0, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=2, difficulty=5)
        third_task = HomeworkTask.objects.create(
            homework=self.hw, test_case_count=0, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=3, difficulty=5)
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 204)
        second_task.refresh_from_db(); third_task.refresh_from_db()
        self.assertEqual(second_task.consecutive_number, 1)
        self.assertEqual(third_task.consecutive_number, 2)

    def test_cannot_delete_from_a_locked_lesson(self):
        self.task.is_under_construction = False
        self.task.save()
        self.lesson.lock_for_construction()
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.task.homework, self.hw)

    def test_normal_user_cant_delete(self):
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.task.homework, self.hw)

    def test_unauth_no_access(self):
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}')
        self.assertEqual(resp.status_code, 401)

    def test_other_teacher_cant_delete(self):
        self.create_teacher_user_and_auth_token()
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.second_teacher_auth_token)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.task.homework, self.hw)

    def test_invalid_task_returns_404(self):
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/111',
            HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 404)

    def test_invalid_lesson_returns_404(self):
        resp = self.client.delete(
            f'/education/course/{self.course.id}/lesson/111/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 404)

    def test_invalid_course_returns_404(self):
        resp = self.client.delete(
            f'/education/course/111/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 404)

    def test_invalid_matching_returns_404(self):
        # try various matcihngs, i.e course and invalid lesson and etc
        self.create_teacher_user_and_auth_token()
        new_course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.second_teacher_auth_user)
        new_lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are you', annexation='bye',
                                            course=new_course)
        new_hw = Homework.objects.create(lesson=new_lesson, is_mandatory=True)
        new_task = HomeworkTask.objects.create(
            homework=new_hw, test_case_count=0, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=1, difficulty=5)

        url_combinations = [
            f'/education/course/{new_course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            f'/education/course/{self.course.id}/lesson/{new_lesson.id}/homework_task/{self.task.id}',
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{new_task.id}'
        ]
        for url_combination in url_combinations:
            resp = self.client.delete(
                url_combination,
                HTTP_AUTHORIZATION=self.teacher_auth_token)
            self.assertTrue(resp.status_code in [403, 404])
            self.task.refresh_from_db()
            self.assertEqual(self.task.homework, self.hw)

