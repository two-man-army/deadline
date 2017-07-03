from django.test import TestCase

from accounts.models import User
from challenges.models import Language
from education.models import Course, Lesson, Homework, HomeworkTask, TaskSubmission, TaskTestCase
from education.tests.factories import HomeworkTaskDescriptionFactory
from education.serializers import TaskTestCaseSerializer

class TaskTestCaseTests(TestCase):
    def setUp(self):
        self.auth_user = User.objects.create(username='tank', email='tank@abv.bg', password='123')
        self.course = Course.objects.create(name='tank', difficulty=1, is_under_construction=False)
        self.lesson = Lesson.objects.create(lesson_number=1, course=self.course, intro='', content='',
                                            annexation='', is_under_construction=False)
        self.hw = Homework.objects.create(is_mandatory=False, lesson=self.lesson)
        self.hw_task = HomeworkTask.objects.create(test_case_count=1, description=HomeworkTaskDescriptionFactory(), is_mandatory=True, consecutive_number=1, difficulty=10,
                                                   homework=self.hw)
        self.lang = Language.objects.create(name='Python')
        self.submission = TaskSubmission.objects.create(author=self.auth_user, code='tank', task=self.hw_task, language=self.lang)

    def test_serialization(self):
        test_case = TaskTestCase.objects.create(
            submission=self.submission, time=1.5, success=True,
            pending=False, description='tanked', error_message='',
            timed_out=False, traceback=''
        )
        received_data = TaskTestCaseSerializer(instance=test_case).data
        expected_data = {'id': test_case.id, 'time': 1.5, 'success': True, 'pending': False, 'description': 'tanked', 'traceback': '', 'error_message': '', 'timed_out': False, 'submission': self.submission.id}

        self.assertEqual(received_data, expected_data)
