import json

from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from education.models import Course, Lesson, Homework, HomeworkTask, HomeworkTaskDescription
from challenges.models import Language


class HomeworkTaskCreateViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.python_language = Language.objects.create(name='Python')
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True)
        self.course.teachers.add(self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.hw = Homework.objects.create(lesson=self.lesson, is_mandatory=True)

    def test_create_task_success(self):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                             data=json.dumps({'description': {'content': 'fix this'},
                                   'is_mandatory': True,
                                   'consecutive_number': 1,
                                   'difficulty': 5,
                                   'supported_languages': [1]}),
                                content_type='application/json')
        hw_task = HomeworkTask.objects.all().first()
        hw_task_desk = HomeworkTaskDescription.objects.all().first()

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(hw_task.is_mandatory, True)
        self.assertEqual(hw_task.consecutive_number, 1)
        self.assertEqual(hw_task.difficulty, 5)
        self.assertEqual(hw_task.supported_languages.first(), self.python_language)
        self.assertEqual(hw_task.description, hw_task_desk)
        self.assertEqual(hw_task.test_case_count, 0)

    def test_create_task_fails_for_non_teacher(self):
        raise NotImplementedError()

    def test_create_task_fails_for_teacher_that_is_not_part_of_course(self):
        raise NotImplementedError()

    def test_create_task_fails_for_course_that_is_not_under_construction(self):
        raise NotImplementedError()

    def test_create_task_fails_for_lesson_that_is_not_under_construction(self):
        raise NotImplementedError()

    def test_create_task_fails_for_lesson_that_is_not_part_of_course(self):
        raise NotImplementedError()

    def test_create_task_fails_for_non_existent_course(self):
        raise NotImplementedError()

    def test_create_task_fails_for_non_existent_lesson(self):
        raise NotImplementedError()