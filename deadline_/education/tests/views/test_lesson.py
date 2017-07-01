from unittest.mock import MagicMock

from django.test import TestCase
from django.http import HttpResponse

from accounts.models import Role, User
from challenges.tests.base import TestHelperMixin
from education.models import Course, Lesson, HomeworkTask, HomeworkTaskDescription, Homework
from education.views import LessonManageView, LessonCreateView, LessonDetailsView


class LessonManagerViewTests(TestCase):
    def test_uses_expected_views_by_method(self):
        self.assertEqual(LessonManageView.VIEWS_BY_METHOD['GET'], LessonDetailsView.as_view)

    def test_get_calls_expected_view(self):
        _old_views = LessonManageView.VIEWS_BY_METHOD

        get_view = MagicMock()
        view_response = MagicMock()
        view_response.return_value = HttpResponse()
        get_view.return_value = view_response
        LessonManageView.VIEWS_BY_METHOD = {'GET': get_view}  # poor man's @patch

        self.client.get(f'/education/course/1/lesson/1')

        get_view.assert_called_once()
        LessonManageView.VIEWS_BY_METHOD = _old_views

    def returns_404_unsupported_method(self):
        resp = self.client.trace(f'/education/course/1/lesson/')
        self.assertEqual(resp.status_code, 404)


class LessonCreateViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=True)
        self.course.teachers.add(self.teacher_auth_user)

    def test_creation(self):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/', HTTP_AUTHORIZATION=self.teacher_auth_token,
                         data={
                             'intro': 'Just Because',
                             'content': 'Just Because',
                             'annexation': 'Just Because',
                             'video_link_1': 'best'
                         })

        self.assertEqual(resp.status_code, 201)
        lesson = Lesson.objects.first()

        self.assertEqual(lesson.lesson_number, 1)
        self.assertEqual(lesson.is_under_construction, True)
        self.assertEqual(lesson.course, self.course)
        self.assertEqual(lesson.annexation, 'Just Because')
        self.assertEqual(lesson.content, 'Just Because')
        self.assertEqual(lesson.intro, 'Just Because')
        self.assertEqual(lesson.video_link_1, 'best')

    def test_forbidden_for_teacher_not_part_of_cours(self):
        teacher_role = Role.objects.filter(name='Teacher').first()
        if teacher_role is None:
            teacher_role = Role.objects.create(name='Teacher')
        sec_teacher = User.objects.create(username='theTeach2', password='123', email='TheTeach2@abv.bg', score=123,
                                                     role=teacher_role)
        sec_teacher_token = 'Token {}'.format(sec_teacher.auth_token.key)
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/', HTTP_AUTHORIZATION=sec_teacher_token,
                                data={
                                    'intro': 'Just Because',
                                    'content': 'Just Because',
                                    'annexation': 'Just Because',
                                    'video_link_1': 'best'
                                })
        self.assertEqual(resp.status_code, 403)

    def test_forbidden_for_non_teacher(self):
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/', HTTP_AUTHORIZATION=self.auth_token,
                                data={
                                    'intro': 'Just Because',
                                    'content': 'Just Because',
                                    'annexation': 'Just Because',
                                    'video_link_1': 'best'
                                })

        self.assertEqual(resp.status_code, 403)

    def test_does_not_create_lesson_for_locked_course(self):
        self.course.is_under_construction = False
        self.course.save()

        resp = self.client.post(f'/education/course/{self.course.id}/lesson/', HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={
                                    'intro': 'Just Because',
                                    'content': 'Just Because',
                                    'annexation': 'Just Because',
                                    'video_link_1': 'best'
                                })

        self.assertEqual(resp.status_code, 400)

    def test_creation_ignores_serializer_fields(self):
        """
        The under_construction, lesson_number and course fields should be ignored and the defaults should be applied:
            lesson_number - the consecutive number this lesson should be
            under_construction - should be True
            course - should be the course given in the URL
        """
        Lesson.objects.create(course=self.course, lesson_number=1)

        # our new lesson should be #2
        resp = self.client.post(f'/education/course/{self.course.id}/lesson/', HTTP_AUTHORIZATION=self.teacher_auth_token,
                                data={
                                    'course': 233,  # should be self.course.id
                                    'is_under_construction': False,
                                    'lesson_number': 50,
                                    'intro': 'Just Because',
                                    'content': 'Just Because',
                                    'annexation': 'Just Because',
                                    'video_link_1': 'best'
                                })
        self.assertEqual(resp.status_code, 201)
        new_lesson = Lesson.objects.last()
        self.assertEqual(new_lesson.course, self.course)
        self.assertEqual(new_lesson.is_under_construction, True)
        self.assertEqual(new_lesson.lesson_number, 2)
        self.assertEqual(new_lesson.intro, 'Just Because')


class LessonDetailViewTests(TestCase, TestHelperMixin):
    def setUp(self):
        self.create_user_and_auth_token()
        self.create_teacher_user_and_auth_token()
        self.course = Course.objects.create(name='teste fundamentals', difficulty=1,
                                            is_under_construction=False)
        self.course.teachers.add(self.teacher_auth_user)
        self.lesson = Lesson.objects.create(lesson_number=1, is_under_construction=False,
                                            intro='hello', content='how are yoou', annexation='bye',
                                            course=self.course)
        self.hw = Homework.objects.create(is_mandatory=False, lesson=self.lesson)
        self.hw_task = HomeworkTask.objects.create(test_case_count=1, description=HomeworkTaskDescription.objects.create(input_format='Hello there', content='tank'),
                                                   is_mandatory=True, consecutive_number=1, difficulty=10,
                                                   homework=self.hw)
        self.hw_task2 = HomeworkTask.objects.create(test_case_count=1, description=HomeworkTaskDescription.objects.create(input_format='Hello there', content='tank'),
                                                   is_mandatory=True, consecutive_number=2, difficulty=10,
                                                   homework=self.hw)

    def test_details_view(self):
        """ Should show some information about all homework task"""
        self.course.enroll_student(self.auth_user)
        resp = self.client.get(f'/education/course/{self.course.id}/lesson/{self.lesson.id}', HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(resp.status_code, 200)
        expected_data = {'id': 1, 'lesson_number': 1, 'is_under_construction': False, 'video_link_1': '',
                         'video_link_2': '', 'video_link_3': '', 'video_link_4': '', 'video_link_5': '',
                         'intro': 'hello', 'content': 'how are yoou', 'annexation': 'bye', 'course': 1,
                         'homework': {'task_count': 2}, 'is_completed': False}

        self.assertEqual(expected_data, resp.data)

    def test_is_forbidden_for_user_not_part_of_course(self):
        resp = self.client.get(f'/education/course/{self.course.id}/lesson/{self.lesson.id}',
                               HTTP_AUTHORIZATION=self.auth_token)
        self.assertEqual(resp.status_code, 403)

    def test_is_forbidden_for_no_user(self):
        resp = self.client.get(f'/education/course/{self.course.id}/lesson/{self.lesson.id}')
        self.assertEqual(resp.status_code, 401)

    def test_is_not_forbidden_for_teacher_or_user_part_of_course(self):
        self.course.enroll_student(self.auth_user)
        resp = self.client.get(f'/education/course/{self.course.id}/lesson/{self.lesson.id}',
                               HTTP_AUTHORIZATION=self.auth_token)
        self.assertNotEqual(resp.status_code, 403)
        resp = self.client.get(f'/education/course/{self.course.id}/lesson/{self.lesson.id}',
                               HTTP_AUTHORIZATION=self.teacher_auth_token)
        self.assertNotEqual(resp.status_code, 403)
