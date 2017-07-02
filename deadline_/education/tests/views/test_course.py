from unittest.mock import MagicMock

from django.test import TestCase
from django.http import HttpResponse

from challenges.tests.base import TestHelperMixin
from education.models import Course
from education.views import CourseManageView, CourseDetailsView
from challenges.models import Language


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
