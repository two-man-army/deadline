from unittest.mock import patch

from django.test import TestCase

from accounts.models import Role, User
from challenges.models import Language
from challenges.tests.base import TestHelperMixin
from education.models import HomeworkTaskDescription, Lesson, Course, Homework, HomeworkTask, TaskSubmission, \
    TaskTestCase


@patch('education.views.run_homework_grader_task')
class TaskSubmissionTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=False)
        self.course.teachers.add(self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=False,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.python_language = Language.objects.create(name="Python")

        self.hw = Homework.objects.create(is_mandatory=False, lesson=self.lesson)
        self.hw_task = HomeworkTask.objects.create(test_case_count=1, description=HomeworkTaskDescription.objects.create(input_format='Hello there', content='tank'),
                                                   is_mandatory=True, consecutive_number=1, difficulty=10,
                                                   is_under_construction=False, homework=self.hw)
        self.hw_task.supported_languages.add(self.python_language)

    def test_normal_submission_works(self, mock_grader_task):
        self.course.enroll_student(self.auth_user)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                   'code': 'print("im at the bottom")',
                                   'language': self.python_language.id
                                })
        self.assertEqual(resp.status_code, 201)
        submission = TaskSubmission.objects.first()
        self.assertEqual(submission.code, 'print("im at the bottom")')
        self.assertEqual(submission.language, self.python_language)
        self.assertEqual(submission.author, self.auth_user)
        self.assertEqual(submission.task, self.hw_task)
        mock_grader_task.assert_called_once()
        # assert that test cases are created
        self.assertEqual(TaskTestCase.objects.count(), self.hw_task.test_case_count)

    def test_submission_does_not_work_while_under_construction(self, mock_grader_task):
        self.course.enroll_student(self.auth_user)
        self.hw_task.is_under_construction = True
        self.hw_task.save()
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })
        self.assertEqual(resp.status_code, 400)
        mock_grader_task.assert_not_called()

    def test_submission_works_for_teacher_while_under_construction(self, mock_grader_task):
        self.hw_task.is_under_construction = True
        self.hw_task.save()
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })
        self.assertEqual(resp.status_code, 201)
        submission = TaskSubmission.objects.first()
        self.assertEqual(submission.code, 'print("im at the bottom")')
        self.assertEqual(submission.language, self.python_language)
        self.assertEqual(submission.author, self.teacher_auth_user)
        self.assertEqual(submission.task, self.hw_task)
        mock_grader_task.assert_called_once()
        # assert that test cases are created
        self.assertEqual(TaskTestCase.objects.count(), self.hw_task.test_case_count)

    def create_new_course_lesson_hw_and_task(self):
        """
            Creates and returns new Course by a new teacher, Lesson, HW and HWTask less boilerplate
            + enrolls self.auth_user to the course
        """
        self.create_teacher_user_and_auth_token()

        new_course = Course.objects.create(name='Ruby Fundamentals', difficulty=1,
                                           is_under_construction=False)
        new_course.teachers.add(self.second_teacher_auth_user)
        new_lesson = Lesson.objects.create(lesson_number=1, is_under_construction=False,
                                           intro='New Lesson', content='Rly New', annexation='No Jokes',
                                           course=new_course)

        hw = Homework.objects.create(is_mandatory=False, lesson=new_lesson)
        new_hw_task = HomeworkTask.objects.create(test_case_count=5, description=HomeworkTaskDescription.objects.create(input_format='Hello there', content='tank'),
                                                  is_mandatory=True, consecutive_number=1, difficulty=10,
                                                  is_under_construction=False, homework=hw)
        new_hw_task.supported_languages.add(self.python_language)
        new_course.enroll_student(self.auth_user)

        return new_course, new_lesson, hw, new_hw_task

    def test_course_lesson_correlation(self, _):
        new_course, *_ = self.create_new_course_lesson_hw_and_task()
        self.course.enroll_student(self.auth_user)

        resp = self.client.post(f'/education/course/{new_course.id}/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_lesson_task_correlation(self, _):
        new_course, new_lesson, hw, new_hw_task = self.create_new_course_lesson_hw_and_task()
        self.course.enroll_student(self.auth_user)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{new_hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['error'], f'Task with ID {new_hw_task.id} does not belong to Lesson with ID {self.lesson.id}')
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_teacher_cannot_access_other_course(self, _):
        new_course, new_lesson, hw, new_hw_task = self.create_new_course_lesson_hw_and_task()
        resp = self.client.post(f'/education/course/{new_course.id}/lesson/{new_lesson.id}/homework_task/{new_hw_task.id}/submission',
                        HTTP_AUTHORIZATION=self.teacher_auth_token,
                        data={
                            'code': 'print("im at the bottom")',
                            'language': self.python_language.id
                        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_unauthorized_cannot_access(self, _):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_unenrolled_user_cannot_access(self, _):
        base_role = Role.objects.filter(name='User').first()
        if base_role is None:
            base_role = Role.objects.create(name='User')
        self.new_user = User.objects.create(username='MnTupo', password='123', email='T{{{@abv.bg', score=123, role=base_role)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_invalid_language_doesnt_work(self, _):
        self.course.enroll_student(self.auth_user)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': 105
                                })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_invalid_course_doesnt_work(self, _):
        self.course.enroll_student(self.auth_user)
        resp = self.client.post(f'/education/course/105/lesson/{self.lesson.id}/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_invalid_lesson_doesnt_work(self, _):
        self.course.enroll_student(self.auth_user)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/105/homework_task/{self.hw_task.id}/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    def test_invalid_task_doesnt_work(self, _):
        self.course.enroll_student(self.auth_user)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/{self.lesson.id}/homework_task/105/submission',
                                HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'code': 'print("im at the bottom")',
                                    'language': self.python_language.id
                                })

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(TaskSubmission.objects.count(), 0)

    # TODO: Test lesson progress
