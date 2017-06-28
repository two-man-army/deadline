from collections import OrderedDict

from django.test import TestCase

from challenges.models import Language
from challenges.tests.base import TestHelperMixin
from education.models import Course, Lesson, Homework, HomeworkTask, HomeworkTaskDescription
from education.serializers import HomeworkSerializer


class HomeworkModelTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='tank', difficulty=1, is_under_construction=False)
        self.lesson = Lesson.objects.create(lesson_number=1, course=self.course, intro='', content='',
                                            annexation='', is_under_construction=False)
        self.python_lang = Language.objects.create(name='Python')

    def test_serialization(self):
        hw = Homework.objects.create(is_mandatory=False, lesson=self.lesson)
        expected_data = {
            'is_mandatory': False,
            'tasks': [{'id': 1, 'description': OrderedDict([('content', 'sup'), ('input_format', ''), ('output_format', ''), ('constraints', ''), ('sample_input', ''), ('sample_output', ''), ('explanation', '')]), 'is_mandatory': True, 'is_under_construction': True, 'consecutive_number': 0, 'difficulty': 5, 'homework': 1, 'supported_languages': ['Python'], 'test_case_count': 0},
                      {'id': 2, 'description': OrderedDict([('content', 'sup'), ('input_format', ''), ('output_format', ''), ('constraints', ''), ('sample_input', ''), ('sample_output', ''), ('explanation', '')]), 'is_mandatory': False, 'is_under_construction': True, 'consecutive_number': 0, 'difficulty': 2, 'homework': 1, 'supported_languages': ['Python'], 'test_case_count': 0},
                      {'id': 3, 'description': OrderedDict([('content', 'sup'), ('input_format', ''), ('output_format', ''), ('constraints', ''), ('sample_input', ''), ('sample_output', ''), ('explanation', '')]), 'is_mandatory': False, 'is_under_construction': True, 'consecutive_number': 0, 'difficulty': 1, 'homework': 1, 'supported_languages': ['Python'], 'test_case_count': 0}]}
        task1 = HomeworkTask.objects.create(homework=hw, description=HomeworkTaskDescription.objects.create(content='sup'), difficulty=5, is_mandatory=True)
        task2 = HomeworkTask.objects.create(homework=hw, description=HomeworkTaskDescription.objects.create(content='sup'), difficulty=2, is_mandatory=False)
        task3 = HomeworkTask.objects.create(homework=hw, description=HomeworkTaskDescription.objects.create(content='sup'), difficulty=1, is_mandatory=False)
        task1.supported_languages.add(self.python_lang)
        task2.supported_languages.add(self.python_lang)
        task3.supported_languages.add(self.python_lang)

        received_data = HomeworkSerializer(hw).data
        self.assertEqual(received_data, expected_data)
