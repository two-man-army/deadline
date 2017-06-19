from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from education.models import Course
from challenges.models import Language


class CourseViewsTests(TestCase, TestHelperMixin):
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
