from unittest.mock import MagicMock

from django.test import TestCase
from django.http import HttpResponse
from rest_framework.test import APITestCase

from challenges.tests.base import TestHelperMixin
from education.models import Course, Lesson
from education.views import CourseManageView, CourseDetailsView, CourseEditView
from challenges.models import Language
from accounts.models import User, Role


class CourseCreateViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.python_lang = Language.objects.create(name='Python')
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()

    def test_creates_course_successfully_with_user(self):
        self.client.post('/education/course', HTTP_AUTHORIZATION=self.teacher_auth_token,
                         data={'name': 'Deadline Test',
                               'difficulty': 5.5,
                               'languages': [1]})
        course: Course = Course.objects.first()
        self.assertIsNotNone(course)
        self.assertEqual(course.name, 'Deadline Test')
        self.assertEqual(course.difficulty, 5.5)
        self.assertEqual(course.teachers.first(), self.teacher_auth_user)
        self.assertEqual(course.teachers.count(), 1)
        self.assertEqual(course.languages.first(), self.python_lang)

    def test_normal_user_cannot_create_course(self):
        response = self.client.post('/education/course', HTTP_AUTHORIZATION=self.auth_token,
                                    data={'name': 'Deadline Test',
                                          'difficulty': 5.5,
                                          'languages': [1]})

        self.assertEqual(response.status_code, 403)
        course: Course = Course.objects.first()
        self.assertIsNone(course)


class CourseManageViewTests(TestCase, TestHelperMixin):
    def test_uses_expected_views_by_method(self):
        self.assertEqual(CourseManageView.VIEWS_BY_METHOD['GET'], CourseDetailsView.as_view)
        self.assertEqual(CourseManageView.VIEWS_BY_METHOD['PATCH'], CourseEditView.as_view)

    def test_get_calls_expected_view(self):
        _old_views = CourseManageView.VIEWS_BY_METHOD

        get_view = MagicMock()
        view_response = MagicMock()
        view_response.return_value = HttpResponse()
        get_view.return_value = view_response
        CourseManageView.VIEWS_BY_METHOD = {'GET': get_view}  # poor man's @patch

        self.client.get(f'/education/course/1')

        get_view.assert_called_once()
        CourseManageView.VIEWS_BY_METHOD = _old_views

    def returns_404_unsupported_method(self):
        resp = self.client.trace(f'/education/course/1')
        self.assertEqual(resp.status_code, 404)


class CourseDetailsViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.python_lang = Language.objects.create(name='Python')
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='Python Fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.course.languages.add(self.python_lang)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='IFs', content='how are you', annexation='bye',
                                            course=self.course)
        self.lesson2 = Lesson.objects.create(lesson_number=2, is_under_construction=True,
                                             intro='Loops', content='how are you', annexation='bye',
                                             course=self.course)

    def test_teacher_can_view(self):
        resp = self.client.get(f'/education/course/{self.course.id}', HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertNotEqual(resp.status_code, 403)
        self.assertEqual(resp.data['name'], 'Python Fundamentals')

    def test_view_returns_data_as_expected(self):
        expected_data = {'name': 'Python Fundamentals', 'difficulty': 1.0, 'languages': ['Python'],
                         'teachers': [{'name': self.teacher_auth_user.username, 'id': 2}],
                         'lessons': [{'consecutive_number': 1, 'short_description': 'IFs'},
                                     {'consecutive_number': 2, 'short_description': 'Loops'}],
                         'main_teacher': {'name': self.course.main_teacher.username,
                                          'id': self.course.main_teacher.id}}

        resp = self.client.get(f'/education/course/{self.course.id}', HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(expected_data, resp.data)

    def test_normal_user_cannot_view_course(self):
        resp = self.client.get(f'/education/course/{self.course.id}', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(resp.status_code, 403)

    def test_enrolled_user_can_view_course(self):
        self.lesson.is_under_construction = False
        self.lesson.save()
        self.lesson2.is_under_construction = False
        self.lesson2.save()
        self.course.is_under_construction = False
        self.course.enroll_student(self.auth_user)
        resp = self.client.get(f'/education/course/{self.course.id}', HTTP_AUTHORIZATION=self.auth_token)
        self.assertNotEqual(resp.status_code, 403)
        self.assertEqual(resp.data['name'], 'Python Fundamentals')

    def test_unauthorized_cannot_view(self):
        resp = self.client.get(f'/education/course/{self.course.id}')
        self.assertEqual(resp.status_code, 401)


class CourseEditViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.rust_lang = Language.objects.create(name='Rust')

    def test_can_edit_name_and_difficulty_while_not_locked(self):
        self.create_teacher_user_and_auth_token()
        self.client.patch(f'/education/course/{self.course.id}',
                          HTTP_AUTHORIZATION=self.teacher_auth_token,
                          data={
                              'name': 'A Man',
                              'difficulty': 8,
                              'main_teacher': self.second_teacher_auth_user.id
                          }, format='json')
        self.course.refresh_from_db()
        self.assertEqual(self.course.difficulty, 8)
        self.assertEqual(self.course.name, 'A Man')
        self.assertEqual(self.course.main_teacher, self.second_teacher_auth_user)
        self.assertTrue(self.second_teacher_auth_user in self.course.teachers.all())

    def test_cannot_edit_while_locked(self):
        self.lesson.lock_for_construction()
        self.course.lock_for_construction()
        resp = self.client.patch(f'/education/course/{self.course.id}',
                                 HTTP_AUTHORIZATION=self.teacher_auth_token,
                                 data={
                                     'name': 'A Man',
                                     'difficulty': 8,
                                 }, format='json')
        self.assertNotEqual(self.course.difficulty, 8)
        self.assertNotEqual(self.course.name, 'A Man')
        self.assertEqual(resp.status_code, 400)

    def test_can_not_edit_languages(self):
        self.client.patch(f'/education/course/{self.course.id}',
                          HTTP_AUTHORIZATION=self.teacher_auth_token,
                          data={
                              'languages': [self.rust_lang.id]
                          })
        self.course.refresh_from_db()
        self.assertNotIn(self.rust_lang, self.course.languages.all())

    def test_cannot_lock_course_while_lesson_not_locked(self):
        resp = self.client.patch(f'/education/course/{self.course.id}',
                          HTTP_AUTHORIZATION=self.teacher_auth_token,
                          data={'is_under_construction': False}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_can_lock_course(self):
        self.lesson.lock_for_construction()
        self.client.patch(f'/education/course/{self.course.id}',
                          HTTP_AUTHORIZATION=self.teacher_auth_token,
                          data={'is_under_construction': False}, format='json')

        self.course.refresh_from_db()
        self.assertEqual(self.course.is_under_construction, False)

    def test_only_main_teacher_can_lock_course(self):
        self.lesson.lock_for_construction()
        self.create_teacher_user_and_auth_token()
        self.course.teachers.add(self.second_teacher_auth_user)
        response = self.client.patch(f'/education/course/{self.course.id}',
                                     HTTP_AUTHORIZATION=self.second_teacher_auth_token,
                                     data={'is_under_construction': False}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.course.is_under_construction, True)

    def test_non_main_teacher_cannot_change_main_teacher(self):
        self.create_teacher_user_and_auth_token()
        self.course.teachers.add(self.second_teacher_auth_user)
        response = self.client.patch(f'/education/course/{self.course.id}',
                          HTTP_AUTHORIZATION=self.second_teacher_auth_token,
                          data={
                              'name': 'A Man',
                              'difficulty': 8,
                              'main_teacher': self.second_teacher_auth_user.id
                          }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(self.course.main_teacher, self.second_teacher_auth_user)
        self.assertNotEqual(self.course.name, 'A Man')

    def test_user_cant_edit(self):
        response = self.client.patch(f'/education/course/{self.course.id}',
                                     HTTP_AUTHORIZATION=self.auth_token,
                                     data={'name': 'Hello'})
        self.assertEqual(response.status_code, 403)

    def test_non_course_teacher_cant_edit(self):
        self.create_teacher_user_and_auth_token()
        response = self.client.patch(f'/education/course/{self.course.id}',
                                     HTTP_AUTHORIZATION=self.second_teacher_auth_token,
                                     data={'name': 'Hello'})
        self.assertEqual(response.status_code, 403)

    def test_cant_lock_while_lesson_is_not_locked(self):
        # The Lesson is not locked and that would raise an error, this should return a 400
        response = self.client.patch(f'/education/course/{self.course.id}',
                                     HTTP_AUTHORIZATION=self.teacher_auth_token,
                                     data={'is_under_construction': False})
        self.course.refresh_from_db()
        self.assertEqual(self.course.is_under_construction, True)
        self.assertEqual(response.status_code, 400)

    def test_cant_lock_twice(self):
        self.lesson.lock_for_construction()
        self.course.lock_for_construction()
        response = self.client.patch(f'/education/course/{self.course.id}',
                                     HTTP_AUTHORIZATION=self.teacher_auth_token,
                                     data={'is_under_construction': False})
        self.course.refresh_from_db()
        self.assertEqual(self.course.is_under_construction, False)
        self.assertEqual(response.status_code, 400)

    def test_cant_unlock_course(self):
        self.lesson.lock_for_construction()
        self.course.lock_for_construction()
        response = self.client.patch(f'/education/course/{self.course.id}',
                                     HTTP_AUTHORIZATION=self.teacher_auth_token,
                                     data={'is_under_construction': True})
        self.course.refresh_from_db()
        self.assertEqual(self.course.is_under_construction, False)  # assure not changed
        self.assertEqual(response.status_code, 400)


class CourseLanguageDeleteViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.rust_lang = Language.objects.create(name='Rust')
        self.python_lang = Language.objects.create(name='Python')
        self.erlang_lang = Language.objects.create(name='Erlang')
        self.course.languages.add(*[self.rust_lang, self.python_lang, self.erlang_lang])

    def test_can_remove_language(self):
        self.assertEqual(self.course.languages.count(), 3)
        response = self.client.delete(f'/education/course/{self.course.id}/language/{self.python_lang.id}',
                                      HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.course.languages.count(), 2)
        self.assertNotIn(self.python_lang, self.course.languages.all())

    def test_cannot_remove_language_when_course_locked(self):
        self.lesson.lock_for_construction()
        self.course.lock_for_construction()
        self.assertEqual(self.course.languages.count(), 3)
        response = self.client.delete(f'/education/course/{self.course.id}/language/{self.python_lang.id}',
                                      HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.course.languages.count(), 3)

    def test_remove_non_existant_language(self):
        self.tank_lang = Language.objects.create(name='Tank')
        response = self.client.delete(f'/education/course/{self.course.id}/language/{self.tank_lang.id}',
                                      HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.course.languages.count(), 3)

    def test_non_teacher_cannot_delete(self):
        response = self.client.delete(f'/education/course/{self.course.id}/language/{self.python_lang.id}',
                                      HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(response.status_code, 403)

    def test_non_existant_course_returns_404(self):
        response = self.client.delete(f'/education/course/21/language/{self.python_lang.id}',
                                      HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(response.status_code, 404)

    def test_non_existant_language_returns_404(self):
        response = self.client.delete(f'/education/course/{self.course.id}/language/444',
                                      HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(response.status_code, 404)

    def test_teacher_on_other_course_cannot_delete(self):
        self.create_teacher_user_and_auth_token()

        course = Course.objects.create(name='teste fundamentals ||', difficulty=1,
                                       is_under_construction=True, main_teacher=self.second_teacher_auth_user)

        response = self.client.delete(f'/education/course/{self.course.id}/language/{self.python_lang.id}',
                                      HTTP_AUTHORIZATION=self.second_teacher_auth_token)
        self.assertEqual(response.status_code, 403)


class CourseLanguageAddViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.rust_lang = Language.objects.create(name='Rust')
        self.python_lang = Language.objects.create(name='Python')
        self.erlang_lang = Language.objects.create(name='Erlang')
        self.coconut_lang = Language.objects.create(name='Coconut')
        self.objective_c_lang = Language.objects.create(name='Objective-C')
        self.course.languages.add(*[self.rust_lang, self.python_lang, self.erlang_lang])

    def test_can_add_language(self):
        self.assertEqual(self.course.languages.count(), 3)
        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    HTTP_AUTHORIZATION=self.teacher_auth_token,
                                    data={'language': self.coconut_lang.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.course.languages.count(), 4)
        self.assertIn(self.coconut_lang, self.course.languages.all())

    def test_cannot_add_language_that_is_there(self):
        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    HTTP_AUTHORIZATION=self.teacher_auth_token,
                                    data={'language': self.python_lang.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.course.languages.count(), 3)

    def test_cannot_add_language_when_course_locked(self):
        self.lesson.lock_for_construction()
        self.course.lock_for_construction()
        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    HTTP_AUTHORIZATION=self.teacher_auth_token,
                                    data={'language': self.coconut_lang.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.course.languages.count(), 3)

    def test_non_teacher_cannot_add(self):
        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    HTTP_AUTHORIZATION=self.auth_token,
                                    data={'language': self.coconut_lang.id})
        self.assertEqual(response.status_code, 403)

    def test_unauth_cant_add(self):
        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    data={'language': self.coconut_lang.id})
        self.assertEqual(response.status_code, 401)

    def test_invalid_course_returns_404(self):
        response = self.client.post(f'/education/course/11/language/',
                                    HTTP_AUTHORIZATION=self.teacher_auth_token,
                                    data={'language': self.coconut_lang.id})
        self.assertEqual(response.status_code, 404)

    def test_invalid_lang_returns_404(self):
        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    HTTP_AUTHORIZATION=self.teacher_auth_token,
                                    data={'language': 444})
        self.assertEqual(response.status_code, 404)

    def test_no_lang_provided_returns_400(self):
        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(response.status_code, 404)

    def test_teacher_on_other_course_cannot_add(self):
        self.create_teacher_user_and_auth_token()

        course = Course.objects.create(name='teste fundamentals ||', difficulty=1,
                                       is_under_construction=True, main_teacher=self.second_teacher_auth_user)

        response = self.client.post(f'/education/course/{self.course.id}/language/',
                                    HTTP_AUTHORIZATION=self.second_teacher_auth_token,
                                    data={'language': self.coconut_lang.id})
        self.assertEqual(response.status_code, 403)


class CourseLessonDeleteViewTests(APITestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True, main_teacher=self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.second_lesson = Lesson.objects.create(lesson_number=2, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)

    def test_can_remove_lesson(self):
        resp = self.client.delete(f'/education/course/{self.course.id}/lesson/{self.lesson.id}',
                                  HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 204)
        self.course.refresh_from_db()
        self.lesson.refresh_from_db()
        self.second_lesson.refresh_from_db()
        self.assertEqual(self.course.lessons.count(), 1)
        self.assertNotIn(self.lesson, self.course.lessons.all())
        self.assertEqual(self.second_lesson.lesson_number, 1)
        # assert that the lesson is not deleted
        self.assertEqual(Lesson.objects.count(), 2)

    def test_cannot_remove_when_lesson_is_locked(self):
        self.lesson.lock_for_construction()
        self.second_lesson.lock_for_construction()
        self.course.lock_for_construction()
        resp = self.client.delete(f'/education/course/{self.course.id}/lesson/{self.lesson.id}',
                                  HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 400)

    def test_normal_user_is_forbidden(self):
        resp = self.client.delete(f'/education/course/{self.course.id}/lesson/{self.lesson.id}',
                                  HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(resp.status_code, 403)

    def test_invalid_course_returns_404(self):
        resp = self.client.delete(f'/education/course/111/lesson/{self.lesson.id}',
                                  HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(resp.status_code, 404)

    def test_invalid_lesson_returns_404(self):
        resp = self.client.delete(f'/education/course/{self.course.id}/lesson/111',
                                  HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(resp.status_code, 404)

    def test_other_teacher_is_forbidden(self):
        self.create_teacher_user_and_auth_token()
        resp = self.client.delete(f'/education/course/{self.course.id}/lesson/{self.lesson.id}',
                                  HTTP_AUTHORIZATION=self.second_teacher_auth_token)
        self.assertEqual(resp.status_code, 403)

    def test_requires_authentication(self):
        resp = self.client.delete(f'/education/course/{self.course.id}/lesson/{self.lesson.id}')
        self.assertEqual(resp.status_code, 401)

    def test_cannot_remove_a_lesson_from_another_course(self):
        new_course = Course.objects.create(name='Dark Cloud', difficulty=1,
                                           is_under_construction=True, main_teacher=self.teacher_auth_user)
        new_lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=new_course)

        resp = self.client.delete(f'/education/course/{self.course.id}/lesson/{new_lesson.id}',
                                  HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 404)
        resp = self.client.delete(f'/education/course/{new_course.id}/lesson/{self.lesson.id}',
                                  HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertEqual(resp.status_code, 404)
