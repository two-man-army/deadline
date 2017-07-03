import unittest
import os
import shutil

from constants import EDUCATION_TEST_FILES_FOLDER
from education.helpers import create_task_test_files


class HelperTests(unittest.TestCase):
    def tearDown(self):
        """
        Deletes the test folders we created
        """
        shutil.rmtree(self.course_folder)
        self.assertFalse(os.path.exists(self.course_folder))

    def test_create_task_test_files_creates_directories_if_not_exist(self):
        self.course_folder = os.path.join(EDUCATION_TEST_FILES_FOLDER, 'tank_course')
        self.lesson_folder = os.path.join(self.course_folder, '2')
        self.task_hw_folder = os.path.join(self.lesson_folder, '2')

        self.assertFalse(os.path.exists(self.course_folder))
        self.assertFalse(os.path.exists(self.lesson_folder))
        self.assertFalse(os.path.exists(self.task_hw_folder))

        create_task_test_files(self.task_hw_folder, 3, "hello", "bye")

        self.assertTrue(os.path.exists(self.course_folder))
        self.assertTrue(os.path.exists(self.lesson_folder))
        self.assertTrue(os.path.exists(self.task_hw_folder))

    def test_create_task_test_files_creates_input_output_files(self):
        self.course_folder = os.path.join(EDUCATION_TEST_FILES_FOLDER, 'tank_course')
        self.lesson_folder = os.path.join(self.course_folder, '2')
        self.task_hw_folder = os.path.join(self.lesson_folder, '2')

        expected_input_file_name = 'input_03.txt'
        input_dir = os.path.join(self.task_hw_folder, expected_input_file_name)
        expected_output_file_name = 'output_03.txt'
        output_dir = os.path.join(self.task_hw_folder, expected_output_file_name)

        rec_inp_dir, rec_otp_dir = create_task_test_files(self.task_hw_folder, 3, "hello\n2", "bye\n2")

        self.assertEqual(rec_inp_dir, input_dir)
        self.assertEqual(rec_otp_dir, output_dir)
        self.assertTrue(os.path.isfile(input_dir))
        self.assertTrue(os.path.isfile(output_dir))
        with open(input_dir) as f:
            self.assertEqual(f.read(), "hello\n2")
        with open(output_dir) as f:
            self.assertEqual(f.read(), "bye\n2")
