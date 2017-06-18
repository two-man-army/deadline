from django.test import TestCase
from django.core.exceptions import ValidationError

from education.models import Course
from challenges.models import Language
from accounts.models import User, Role


class CourseModelTests(TestCase):
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
        teacher_role = Role.objects.create(name='teacher')
        us = User.objects.create(username='123', password='1,23', email='123@abv.bg', role=base_role)

        c = Course.objects.create(name='Algo', difficulty=1)
        with self.assertRaises(ValidationError):
            c.teachers.add(us)
            c.full_clean()
