import json

from django.test import TestCase

from accounts.models import Role, User
from challenges.tests.base import TestHelperMixin
from challenges.models import Language
from education.models import Course, Lesson, Homework, HomeworkTask, HomeworkTaskDescription


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
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_create_task_fails_for_teacher_that_is_not_part_of_course(self):
        teacher_role = Role.objects.filter(name='Teacher').first()
        second_teacher = User.objects.create(username='theTeach2', password='123', email='TheTeach2@abv.bg', score=123,
                                                     role=teacher_role)
        second_teacher_token = 'Token {}'.format(second_teacher.auth_token.key)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=second_teacher_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data['error'], 'You do not have permission to create Course Homework!')

    def test_create_task_fails_for_course_that_is_not_under_construction(self):
        self.course.is_under_construction = False
        self.course.save()
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 400)

    def test_create_task_fails_for_lesson_that_is_not_under_construction(self):
        self.lesson.is_under_construction = False
        self.lesson.save()
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 400)

    def test_create_task_fails_for_lesson_that_is_not_part_of_course(self):
        """
        Create a new course and a new lesson which are completely separate from ours
            and try to add a Task to the new lesson by adding the OLD course_id
        """
        new_course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True)
        new_course.teachers.add(self.teacher_auth_user)
        new_lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=new_course)
        hw = Homework.objects.create(lesson=new_lesson, is_mandatory=True)

        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{new_lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['error'], 'Lesson with ID 2 does not belong to Course with ID 1')

    def test_create_task_fails_for_non_existent_course(self):
        resp = self.client.post(f'/education/course/151/lesson/{self.lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.data['error'], 'Course with ID 151 does not exist.')

    def test_create_task_fails_for_non_existent_lesson(self):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/151/homework_task/',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.data['error'], 'Lesson with ID 151 does not exist.')
