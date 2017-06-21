from django.test import TestCase

from challenges.tests.base import TestHelperMixin
from education.models import Course, Lesson, UserLessonProgress, UserCourseProgress


class UserLessonProgressModelTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.course = Course.objects.create(name='tank', difficulty=1, is_under_construction=False)
        self.course_progress = UserCourseProgress.objects.create(user=self.auth_user, course=self.course)
        self.lesson = Lesson.objects.create(lesson_number=1, course=self.course, intro='', content='', annexation='', is_under_construction=False)

    def test_normal_creation(self):
        lesson_progress = UserLessonProgress.objects.create(user=self.auth_user, lesson=self.lesson,
                                                            is_complete=False, course_progress=self.course_progress)
        self.assertEqual(lesson_progress.user, self.auth_user)
        self.assertEqual(lesson_progress.lesson, self.lesson)
        self.assertEqual(lesson_progress.course_progress, self.course_progress)

    def test_cannot_create_without_course_progress(self):
        with self.assertRaises(Exception):
            UserLessonProgress.objects.create(user=self.auth_user, lesson=self.lesson, is_complete=False)

    def test_cannot_create_with_course_progress_for_another_course(self):
        """ The CourseProgress and Lesson's Course must be about the same Course!"""
        self.course_2 = Course.objects.create(name='tank2', difficulty=5, is_under_construction=False)
        other_course_progress = UserCourseProgress.objects.create(user=self.auth_user, course=self.course_2)

        with self.assertRaises(Exception):
            UserLessonProgress.objects.create(user=self.auth_user, lesson=self.lesson, is_complete=False, course_progress=other_course_progress)

    def test_cannot_create_with_course_progress_for_another_user(self):
        from accounts.models import User
        new_user = User.objects.create(username='tank', password='123', email='fam@abv.bg')
        foreign_course_progress = UserCourseProgress.objects.create(user=self.auth_user, course=self.course)

        with self.assertRaises(Exception):
            UserLessonProgress.objects.create(user=new_user, lesson=self.lesson, is_complete=False, course_progress=foreign_course_progress)

    def test_cannot_create_lesson_progress_while_course_is_under_construction(self):
        self.course.is_under_construction = True
        with self.assertRaises(Exception):
            UserLessonProgress.objects.create(user=self.auth_user, lesson=self.lesson,
                                              is_complete=False, course_progress=self.course_progress)

    def test_cannot_create_lesson_progress_while_lesson_is_under_construction(self):
        self.course.is_under_construction = False
        self.assertFalse(self.course.is_under_construction)
        self.lesson.is_under_construction = True
        with self.assertRaises(Exception):
            UserLessonProgress.objects.create(user=self.auth_user, lesson=self.lesson,
                                              is_complete=False, course_progress=self.course_progress)
