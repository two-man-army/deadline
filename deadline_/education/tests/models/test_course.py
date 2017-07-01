from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from education.serializers import CourseSerializer
from education.models import Course
from challenges.models import Language
from accounts.models import User, Role


class CourseModelTests(TestCase):
    def test_has_teacher(self):
        teacher_role = Role.objects.create(name='teacher')
        us = User.objects.create(username='tank', email='tank@abv.bg', password='tank0', role=teacher_role)
        c = Course.objects.create(name='Algo', difficulty=1)

        self.assertFalse(c.has_teacher(us))
        c.teachers.add(us)
        self.assertTrue(c.has_teacher(us))

    def test_has_student(self):
        from education.models import UserCourseProgress
        us = User.objects.create(username='tank', email='tank@abv.bg', password='tank0')
        c = Course.objects.create(name='Algo', difficulty=1)
        c.is_under_construction = False

        self.assertFalse(c.has_student(us))
        UserCourseProgress.objects.create(course=c, user=us)
        self.assertTrue(c.has_student(us))

    def test_newly_created_course_is_under_construction(self):
        c = Course.objects.create(name='Algo', difficulty=1)
        self.assertTrue(c.is_under_construction)

    def test_cannot_have_three_digit_or_invalid_difficulty(self):
        test_difficulties = [1.11, 1.111, 1.55, 1.4999]  # should all raise
        for diff in test_difficulties:
            c = Course.objects.create(name='Algo', difficulty=diff)

            with self.assertRaises(ValidationError):
                c.full_clean()

        c = Course.objects.create(name='Hello For The Last Time', difficulty=1.5)
        c.full_clean()  # should not raise

    def test_cannot_have_base_user_as_teacher(self):
        base_role = Role.objects.create(name='base')
        teacher_role = Role.objects.create(name='Teacher')
        us = User.objects.create(username='123', password='1,23', email='123@abv.bg', role=base_role)

        c = Course.objects.create(name='Algo', difficulty=1)
        with self.assertRaises(ValidationError):
            c.teachers.add(us)
            c.full_clean()

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
