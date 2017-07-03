from django.test import TestCase

from education.models import TaskSubmission, HomeworkTask, Course, Lesson, Homework
from challenges.models import Language
from accounts.models import User
from education.tests.factories import HomeworkTaskDescriptionFactory
from education.serializers import TaskSubmissionSerializer


class TaskSubmissionTests(TestCase):
    def setUp(self):
        self.auth_user = User.objects.create(username='tank', email='aa@abv.bg', password='123')
        self.python_language = Language.objects.create(name='Python')
        self.course = Course.objects.create(name='Rob Bailey', difficulty=1,
                                            is_under_construction=True)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=True,
                                            intro='hello', content='how are you', annexation='bye',
                                            course=self.course)
        self.hw = Homework.objects.create(lesson=self.lesson, is_mandatory=True)
        self.task = HomeworkTask.objects.create(
            homework=self.hw, test_case_count=0, description=HomeworkTaskDescriptionFactory(),
            is_mandatory=True, consecutive_number=1, difficulty=5)

    def test_can_save_duplicate_submission(self):
        s = TaskSubmission(language=self.python_language, task=self.task, author=self.auth_user, code="")
        s.save()
        s = TaskSubmission(language=self.python_language, task=self.task, author=self.auth_user, code="")
        s.save()

        self.assertEqual(TaskSubmission.objects.count(), 2)

    def test_cannot_save_blank_submission(self):
        s = TaskSubmission(language=self.python_language, task=self.task, author=self.auth_user, code='')
        with self.assertRaises(Exception):
            s.full_clean()

    def test_serialization(self):
        data = {'task': self.task.id, 'language': self.python_language.id, 'code': 'tank', 'author': self.auth_user.id}
        ser = TaskSubmissionSerializer(data=data)
        self.assertTrue(ser.is_valid())
        instance = ser.save()

        self.assertEqual(instance.code, 'tank')
        self.assertEqual(instance.language, self.python_language)
        self.assertEqual(instance.task, self.task)
        self.assertEqual(instance.author, self.auth_user)

    def test_serialization_ignores_default_fields(self):
        """
        There are some fields, like is_solved which should be False regardless of what data is given
        """
        data = {'task': self.task.id, 'language': self.python_language.id, 'code': 'tank', 'author': self.auth_user.id,
                'is_solved': True, 'grading_is_pending': False, 'timed_out': True}
        ser = TaskSubmissionSerializer(data=data)
        self.assertTrue(ser.is_valid())
        instance = ser.save()

        self.assertEqual(instance.is_solved, False)
        self.assertEqual(instance.grading_is_pending, True)
        self.assertEqual(instance.timed_out, False)
