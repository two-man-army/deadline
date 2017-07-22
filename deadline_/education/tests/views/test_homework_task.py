import json

from django.test import TestCase
from rest_framework.test import APITestCase

from accounts.models import Role, User
from challenges.tests.base import TestHelperMixin
from challenges.models import Language
from education.models import Course, Lesson, Homework, HomeworkTask, HomeworkTaskDescription
from education.tests.factories import HomeworkTaskDescriptionFactory
from education.views import HomeworkTaskManageView, HomeworkTaskEditView, HomeworkTaskTestCreateView, LessonHomeworkTaskDeleteView


class HomeworkTaskManageViewTests(TestCase):
    def test_uses_expected_views_by_method(self):
        self.assertEqual(HomeworkTaskManageView.VIEWS_BY_METHOD['PATCH'], HomeworkTaskEditView.as_view)
        self.assertEqual(HomeworkTaskManageView.VIEWS_BY_METHOD['DELETE'], LessonHomeworkTaskDeleteView.as_view)


class HomeworkTaskCreateViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.python_language = Language.objects.create(name='Python')
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
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
        self.create_teacher_user_and_auth_token()
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/',
                                HTTP_AUTHORIZATION=self.second_teacher_auth_token,
                                data=json.dumps({'description': {'content': 'fix this'},
                                                 'is_mandatory': True,
                                                 'consecutive_number': 1,
                                                 'difficulty': 5,
                                                 'supported_languages': [1]}),
                                content_type='application/json')

        self.assertEqual(resp.status_code, 403)

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
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
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


class HomeworkTaskEditViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.python_language = Language.objects.create(name='Python')
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.hw = Homework.objects.create(lesson=self.lesson, is_mandatory=True)
        self.task = HomeworkTask.objects.create(
            homework=self.hw, test_case_count=2, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=1, difficulty=5)
        self.task.supported_languages.add(self.python_language)

    def test_can_edit(self):
        resp = self.client.patch(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
                          HTTP_AUTHORIZATION=self.teacher_auth_token,
                          data={
                            'is_mandatory': False,
                            'description': {
                                'content': 'tank'
                            }
                          }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.task.description.refresh_from_db()
        self.assertEqual(self.task.is_mandatory, False)
        self.assertEqual(self.task.description.content, 'tank')

    def test_can_lock_task_ignores_other_fields(self):
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token,
            data={
                'is_under_construction': False,
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertNotEqual(self.task.is_mandatory, False)
        self.assertEqual(self.task.is_under_construction, False)
        self.assertNotEqual(self.task.description.content, 'tank')

    def test_non_main_teacher_cant_lock_task(self):
        self.create_teacher_user_and_auth_token()
        self.course.teachers.add(self.second_teacher_auth_user)
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.second_teacher_auth_token,
            data={
                'is_under_construction': False
            }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.task.refresh_from_db()
        self.assertEqual(self.task.is_under_construction, True)

    def test_cannot_lock_twice(self):
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token, data={'is_under_construction': False}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.is_under_construction, False)
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token, data={'is_under_construction': False}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_cannot_unlock_task(self):
        self.task.lock_for_construction()
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token, data={'is_under_construction': True}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.task.is_under_construction, False)

    def test_cannot_edit_uneditable_fields(self):
        # test_case_count, homework, supported_languages,
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token,
            data={
                'test_case_count': 100,
                'homework': 1,
                'supported_languages': [1, 2]
            },
            format='json')
        self.assertEqual(resp.status_code, 400)
        self.task.refresh_from_db()
        self.assertNotEqual(self.task.test_case_count, 100)
        self.assertNotEqual(self.task.homework_id, -1)
        self.assertNotEqual(self.task.supported_languages.count(), 2)

    def test_cannot_edit_if_task_locked(self):
        self.task.lock_for_construction()
        # only allow description to be edited when the task is locked
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token,
            data={
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertNotEqual(self.task.is_mandatory, False)
        self.assertNotEqual(self.task.description.content, 'tank')

        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token,
            data={
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.task.description.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.task.description.content, 'tank')

    def test_normal_user_cannot_access(self):
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.auth_token,
            data={
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_other_teacher_cannot_access(self):
        self.create_teacher_user_and_auth_token()
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.second_teacher_auth_token,
            data={
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_unauth_401(self):
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            data={
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_invalid_course_mashups(self):
        # Mash up URLs with different courses
        self.create_teacher_user_and_auth_token()
        new_course = Course.objects.create(name='teste fundamentals ||', difficulty=1,
                                            is_under_construction=True, main_teacher=self.second_teacher_auth_user)
        new_lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=new_course)
        new_hw = Homework.objects.create(lesson=new_lesson, is_mandatory=True)
        new_task = HomeworkTask.objects.create(
            homework=new_hw, test_case_count=2, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=1, difficulty=5)
        new_task.supported_languages.add(self.python_language)

        expected_status_codes = [403, 404]
        urls = [
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{new_task.id}',
            f'/education/course/{self.course.id}/lesson/{new_lesson.id}/homework_task/{self.task.id}',
            f'/education/course/{new_course.id}/lesson/{self.lesson.id}/homework_task/{self.task.id}',
        ]
        for url in urls:
            resp = self.client.patch(
                url,
                HTTP_AUTHORIZATION=self.teacher_auth_token,
                data={
                    'is_mandatory': False,
                    'description': {
                        'content': 'tank'
                    }
                }, format='json')
            self.assertIn(resp.status_code, expected_status_codes)

    def test_invalid_task_404(self):
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/111',
            HTTP_AUTHORIZATION=self.teacher_auth_token,
            data={
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 404)

    def test_invalid_lesson_404(self):
        resp = self.client.patch(
            f'/education/course/{self.course.id}/lesson/111/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token,
            data={
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 404)

    def test_invalid_course_404(self):
        resp = self.client.patch(
            f'/education/course/111/lesson/{self.lesson.id}/homework_task/{self.task.id}',
            HTTP_AUTHORIZATION=self.teacher_auth_token,
            data={
                'is_mandatory': False,
                'description': {
                    'content': 'tank'
                }
            }, format='json')
        self.assertEqual(resp.status_code, 404)
