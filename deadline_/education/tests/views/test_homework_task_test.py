from unittest.mock import patch

from django.test import TestCase

from accounts.models import Role, User
from challenges.tests.base import TestHelperMixin
from challenges.models import Language
from education.tests.factories import HomeworkTaskDescriptionFactory
from education.models import Course, Lesson, Homework, HomeworkTask, HomeworkTaskTest


@patch('education.helpers.create_task_test_files')
class HomeworkTaskCreateViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.python_language = Language.objects.create(name='Python')
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True)
        self.course.teachers.add(self.teacher_auth_user)
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

        task_test: HomeworkTaskTest = HomeworkTaskTest.objects.first()

        mock_create_task.assert_called_once_with(course_name=self.course.name, lesson_number=self.lesson.lesson_number,
                                                 task_number=self.task.consecutive_number,
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
        teacher_role = Role.objects.filter(name='Teacher').first()
        second_teacher = User.objects.create(username='theTeach2', password='123', email='TheTeach2@abv.bg', score=123,
                                             role=teacher_role)
        second_teacher_token = 'Token {}'.format(second_teacher.auth_token.key)

        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=second_teacher_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(HomeworkTaskTest.objects.count(), 0)

    def test_create_test_fails_course_that_is_not_under_construction(self, _):
        self.course.is_under_construction = False
        self.course.save()

        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)

    def test_create_test_fails_lesson_that_is_not_under_construction(self, _):
        self.lesson.is_under_construction = False
        self.lesson.save()

        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}/test',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={"input": self.input, "output": self.output})

        self.assertEqual(resp.status_code, 403)

    def test_create_test_fails_homework_task_that_is_not_under_construction(self, _):
        raise NotImplementedError()

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
                                            is_under_construction=True)
        course_two.teachers.add(self.teacher_auth_user)
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
                                           is_under_construction=True)
        course_two.teachers.add(self.teacher_auth_user)
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
