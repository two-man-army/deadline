from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from education.models import Course, Lesson, UserCourseProgress


class UserCourseProgressModelTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.course = Course.objects.create(name='tank', difficulty=1, is_under_construction=False)
        self.course_progress = UserCourseProgress.objects.create(user=self.auth_user, course=self.course)
        self.lesson = Lesson.objects.create(lesson_number=1, course=self.course, intro='', content='', annexation='', is_under_construction=False)

    def test_normal_creation(self):
        course_progress = UserCourseProgress(user=self.auth_user, course=self.course)

        self.assertEqual(course_progress.user, self.auth_user)
        self.assertEqual(course_progress.course, self.course)

    def test_cannot_create_while_some_lesson_is_under_construction(self):
        # create a Lesson that is under_construction
        Lesson.objects.create(lesson_number=2, course=self.course, intro='', content='', annexation='',
                                             is_under_construction=True)
        self.course.refresh_from_db()

        with self.assertRaises(Exception):
            UserCourseProgress.objects.create(user=self.auth_user, course=self.course)

    def test_cannot_create_while_course_is_under_construction(self):
        self.course.is_under_construction = True

        with self.assertRaises(Exception):
            UserCourseProgress.objects.create(user=self.auth_user, course=self.course)