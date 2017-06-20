from io import BytesIO

from django.test import TestCase
from rest_framework.parsers import JSONParser

from education.models import HomeworkTaskDescription
from education.serializers import HomeworkTaskDescriptionSerializer


class HomeworkTaskDescriptionTests(TestCase):
    def test_serialization(self):
        expected_dict = {'content': 'tank', 'input_format': 'none', 'output_format': 'some', 'constraints': 'lol', 'sample_input': '', 'sample_output': '', 'explanation': 'hello'}

        hw_desc = HomeworkTaskDescription.objects.create(
            content='tank', input_format='none',
            output_format='some', constraints='lol',
            explanation='hello'
        )

        serializer = HomeworkTaskDescriptionSerializer(instance=hw_desc)
        self.assertEqual(serializer.data, expected_dict)

    def test_deserialization_all_fields(self):
        json = b'{"content": "tank", ' \
               b'"input_format":"1", "output_format": "2", "constraints": "none",' \
               b'"sample_input":"bad", "sample_output":"lol", "explanation":"wokeup"}'
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = HomeworkTaskDescriptionSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        hw_desc = serializer.save()

        self.assertEqual(hw_desc.content, 'tank')
        self.assertEqual(hw_desc.explanation, 'wokeup')
        self.assertEqual(hw_desc.input_format, '1')
        self.assertEqual(hw_desc.output_format, '2')
        self.assertEqual(hw_desc.constraints, 'none')
        self.assertEqual(hw_desc.sample_input, 'bad')
        self.assertEqual(hw_desc.sample_output, 'lol')

    def test_deserialization_with_one_field(self):
        json = b'{"content": "tank"}'
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = HomeworkTaskDescriptionSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        hw_desc = serializer.save()

        self.assertEqual(hw_desc.content, 'tank')
        self.assertEqual(hw_desc.input_format, '')

