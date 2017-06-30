from unittest.mock import MagicMock

from django.test import TestCase
from django.http import HttpResponse

from accounts.models import Role, User
from challenges.tests.base import TestHelperMixin
from education.models import Course, Lesson
from education.views import LessonManageView, LessonCreateView


class LessonManagerViewTests(TestCase):
    def test_uses_expected_views_by_method(self):
        self.assertEqual(LessonManageView.VIEWS_BY_METHOD['POST'], LessonCreateView.as_view)

    def test_post_calls_expected_view(self):
        _old_views = LessonManageView.VIEWS_BY_METHOD

        post_view = MagicMock()
        view_response = MagicMock()
        view_response.return_value = HttpResponse()
        post_view.return_value = view_response
        LessonManageView.VIEWS_BY_METHOD = {'POST': post_view} # poor man's patch

        self.client.post(f'/education/course/1/lesson/')

        post_view.assert_called_once()
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
                                            is_under_construction=True)
        self.course.teachers.add(self.teacher_auth_user)

    def test_tank(self):
        print(self.client.get(f'/education/course/{self.course.id}/lesson', HTTP_AUTHORIZATION=self.auth_token))