from django.test import TestCase
from django.db.utils import IntegrityError

from education.tests.factories import HomeworkTaskDescriptionFactory
from education.models import Homework, HomeworkTask, HomeworkTaskDescription
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

