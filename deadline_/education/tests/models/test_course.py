from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from accounts.models import User, Role
from challenges.models import Language
from education.serializers import CourseSerializer
from education.models import Course, UserLessonProgress, UserCourseProgress, Lesson
from education.errors import StudentAlreadyEnrolledError, InvalidEnrollmentError, InvalidLockError, AlreadyLockedError


class CourseModelTests(TestCase):
    def setUp(self):
        self.c = Course.objects.create(name='Algo', difficulty=1, is_under_construction=True)

    def test_has_teacher(self):
        teacher_role = Role.objects.create(name='teacher')
        us = User.objects.create(username='tank', email='tank@abv.bg', password='tank0', role=teacher_role)

        self.assertFalse(self.c.has_teacher(us))
        self.c.teachers.add(us)
        self.assertTrue(self.c.has_teacher(us))

    def test_has_student(self):
        us = User.objects.create(username='tank', email='tank@abv.bg', password='tank0')

        self.c.is_under_construction = False

        self.assertFalse(self.c.has_student(us))
        UserCourseProgress.objects.create(course=self.c, user=us)
        self.assertTrue(self.c.has_student(us))

    def test_newly_created_course_is_under_construction(self):

        self.assertTrue(self.c.is_under_construction)

    def test_cannot_have_three_digit_or_invalid_difficulty(self):
        test_difficulties = [1.11, 1.111, 1.55, 1.4999]  # should all raise
        for diff in test_difficulties:
            c = Course.objects.create(name='Algo', difficulty=diff)

            with self.assertRaises(ValidationError):
                c.full_clean()

        c = Course.objects.create(name='Hello For The Last Time', difficulty=1.5)
        self.c.full_clean()  # should not raise

    def test_cannot_have_base_user_as_teacher(self):
        base_role = Role.objects.create(name='base')
        teacher_role = Role.objects.create(name='Teacher')
        us = User.objects.create(username='123', password='1,23', email='123@abv.bg', role=base_role)


        with self.assertRaises(ValidationError):
            self.c.teachers.add(us)
            self.c.full_clean()

    def test_deserialization(self):
        takn_lang = Language.objects.create(name="takn")
        json = b'{"name":"Deadline Test", "difficulty":5.5, "languages": [1]}'
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = CourseSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        course = serializer.save()

        self.assertEqual(course.name, 'Deadline Test')
        self.assertEqual(course.difficulty, 5.5)
        self.assertEqual(course.languages.first(), takn_lang)

    def test_deserialization_with_user(self):
        takn_lang = Language.objects.create(name="takn")
        user = User.objects.create(username='tank', email='tank@abv.bg', password='1234')
        json = b'{"name":"Deadline Test", "difficulty":5.5, "languages": [1]}'
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = CourseSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        course = serializer.save(teachers=[user])

        self.assertEqual(course.name, 'Deadline Test')
        self.assertEqual(course.difficulty, 5.5)
        self.assertEqual(course.teachers.first(), user)
        self.assertEqual(course.languages.first(), takn_lang)

    def test_enroll_student_enrolls_student(self):
        """ Should add him to the students list and create a UserCourseProgress and UserLessonprogress for each lesson"""
        us = User.objects.create(username='123', password='1,23', email='123@abv.bg')
        # create lessons to the course
        l1 = Lesson.objects.create(course=self.c, intro='', lesson_number=1, is_under_construction=False)
        l2 = Lesson.objects.create(course=self.c, intro='', lesson_number=2, is_under_construction=False)
        l3 = Lesson.objects.create(course=self.c, intro='', lesson_number=3, is_under_construction=False)
        self.assertEqual(self.c.lessons.count(), 3)
        self.assertEqual(UserCourseProgress.objects.count(), 0)
        self.assertEqual(UserLessonProgress.objects.count(), 0)
        self.assertFalse(self.c.has_student(us))

        self.c.is_under_construction = False
        self.c.enroll_student(us)

        self.assertTrue(self.c.has_student(us))
        self.assertEqual(UserCourseProgress.objects.count(), 1)
        self.assertEqual(UserLessonProgress.objects.count(), 3)
        course_progress = UserCourseProgress.objects.first()
        self.assertEqual(course_progress.user, us)
        self.assertEqual(course_progress.course, self.c)

        for lesson in [l1, l2, l3]:
            lesson_progress = UserLessonProgress.objects.filter(lesson=lesson).first()
            self.assertEqual(lesson_progress.course_progress, course_progress)
            self.assertEqual(lesson_progress.user, us)

    def test_cannot_enroll_same_student_twice(self):
        us = User.objects.create(username='123', password='1,23', email='123@abv.bg')
        self.c.is_under_construction = False
        self.c.enroll_student(us)
        with self.assertRaises(StudentAlreadyEnrolledError):
            self.c.enroll_student(us)

    def test_cannot_enroll_student_while_under_construction(self):
        us = User.objects.create(username='123', password='1,23', email='123@abv.bg')
        self.c.is_under_construction = True
        with self.assertRaises(InvalidEnrollmentError):
            self.c.enroll_student(us)

    def test_lock_can_lock(self):
        self.c.lock_for_construction()
        self.assertEqual(self.c.is_under_construction, False)

    def test_lock_cannot_lock_twice(self):
        self.c.lock_for_construction()
        with self.assertRaises(AlreadyLockedError):
            self.c.lock_for_construction()

    @patch('education.models.Course.can_lock')
    def test_lock_cannot_lock_when_not_eligible_for_lock(self, mock_can_lock):
        mock_can_lock.return_value = False
        with self.assertRaises(InvalidLockError):
            self.c.lock_for_construction()

    def test_can_lock_if_lessons_are_locked(self):
        Lesson.objects.create(course=self.c, is_under_construction=False, lesson_number=1)
        self.c.refresh_from_db()
        self.assertTrue(self.c.can_lock())

    def test_can_lock_cant_lock_if_lessons_are_not_locked(self):
        Lesson.objects.create(course=self.c, is_under_construction=False, lesson_number=1)
        Lesson.objects.create(course=self.c, is_under_construction=True, lesson_number=2)
        self.assertFalse(self.c.can_lock())
