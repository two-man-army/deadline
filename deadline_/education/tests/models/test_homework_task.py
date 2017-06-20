from collections import OrderedDict
from io import BytesIO

from django.test import TestCase
from django.db.utils import IntegrityError
from rest_framework.parsers import JSONParser

from education.tests.factories import HomeworkTaskDescriptionFactory
from education.models import Homework, HomeworkTask, HomeworkTaskDescription
from education.serializers import HomeworkTaskSerializer
from challenges.models import Language


class HomeworkTaskModelTests(TestCase):
    def setUp(self):
        self.hw = Homework.objects.create()
        self.python_lang = Language.objects.create(name='Python')

    def test_cannot_create_task_without_assigning_homework(self):
        with self.assertRaises(IntegrityError) as e:
            HomeworkTask.objects.create(test_case_count=1, description=HomeworkTaskDescriptionFactory(), is_mandatory=True, consecutive_number=1, difficulty=10)

    def test_creation_works(self):
        HomeworkTask.objects.create(test_case_count=1, description=HomeworkTaskDescriptionFactory(), is_mandatory=True,
                                    consecutive_number=1, difficulty=10,
                                    homework=self.hw)

    def test_deserialization_with_nested_description(self):
        """ Should create the description object as well """
        json = b'{"homework": 1, "test_case_count": 5, "supported_languages": [1],' \
               b'"description": {"content": "tank"}, "is_mandatory":true, "consecutive_number": 1,' \
               b'"difficulty": 1}'
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = HomeworkTaskSerializer(data=data)
        serializer.is_valid()
        hw_task = serializer.save()

        self.assertEqual(hw_task.homework, self.hw)
        self.assertEqual(hw_task.test_case_count, 5)
        self.assertEqual(hw_task.supported_languages.count(), 1)
        self.assertEqual(hw_task.supported_languages.first(), self.python_lang)
        self.assertEqual(hw_task.is_mandatory, True)
        self.assertEqual(hw_task.description, HomeworkTaskDescription.objects.first())
        self.assertEqual(hw_task.difficulty, 1)
        self.assertEqual(hw_task.consecutive_number, 1)

    def test_serialization(self):
        expected_json = {
            'id': 1, 'description': OrderedDict([('content', 'tank'), ('input_format', ''),
                                                 ('output_format', ''), ('constraints', ''), ('sample_input', ''),
                                                 ('sample_output', ''), ('explanation', '')]),
            'supported_languages': ['Python'],
            'test_case_count': 5, 'is_mandatory': True, 'consecutive_number': 1, 'difficulty': 1, 'homework': 1}

        hw_task = HomeworkTask.objects.create(homework=self.hw, test_case_count=5,
                                              description=HomeworkTaskDescription.objects.create(content='tank'),
                                              is_mandatory=True, consecutive_number=1,
                                              difficulty=1)

        hw_task.supported_languages.add(self.python_lang)
        hw_task.refresh_from_db()
        ser = HomeworkTaskSerializer(instance=hw_task)
        print(ser.data)
        self.assertEqual(ser.data, expected_json)