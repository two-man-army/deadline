from io import BytesIO

from django.test import TestCase
from rest_framework.parsers import JSONParser

from accounts.models import User
from education.errors import AlreadyLockedError, InvalidLockError
from education.models import Course, Lesson, Homework, HomeworkTask
from education.serializers import LessonSerializer
from education.tests.factories import HomeworkTaskDescriptionFactory


class CourseModelTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name='tank', difficulty=1, main_teacher=User.objects.create(email='tank@abv.bg', password='tank0'))

    def create_lesson(self):
        return Lesson.objects.create(lesson_number=1,
                              video_link_1='youtube.com/tank', course=self.course,
                              intro='Today we will tank',
                              content='Tank much')

    def test_creation(self):
        less = self.create_lesson()
        self.course.refresh_from_db()

        self.assertEqual(less.course, self.course)
        self.assertEqual(less.video_link_1, 'youtube.com/tank')
        self.assertEqual(less.annexation, '')
        self.assertEqual(self.course.lessons.count(), 1)
        self.assertEqual(self.course.lessons.first(), less)
        self.assertTrue(less.is_under_construction)

    def test_can_lock(self):
        less = self.create_lesson()
        can_lock, msg = less.can_lock()
        self.assertTrue(can_lock)
        self.assertEqual(msg, '')

    def test_cant_lock_if_task_under_construction(self):
        less = self.create_lesson()
        hw = Homework.objects.create(lesson=less, is_mandatory=True)
        HomeworkTask.objects.create(homework=hw, is_under_construction=True, is_mandatory=True, difficulty=1,
                                    description=HomeworkTaskDescriptionFactory())
        can_lock, msg = less.can_lock()
        self.assertFalse(can_lock)
        self.assertEqual(msg, 'Cannot lock the Lesson while a HomeworkTask is under construction')

    def test_cant_lock_if_already_locked(self):
        less = self.create_lesson()
        less.is_under_construction = False
        can_lock, msg = less.can_lock()
        self.assertFalse(can_lock)
        self.assertEqual(msg, 'Cannot lock an already locked Lesson')

    def test_get_course_returns_course(self):
        received_course = self.create_lesson().get_course()
        self.assertEqual(received_course, self.course)

    def test_lesson_lock_sets_under_construction_to_false(self):
        less = self.create_lesson()
        self.assertTrue(less.is_under_construction)
        less.lock_for_construction()
        self.assertFalse(less.is_under_construction)

    def test_double_lesson_lock_raises_exception(self):
        less = self.create_lesson()
        less.lock_for_construction()
        with self.assertRaises(AlreadyLockedError):
            less.lock_for_construction()

    def test_lock_raises_if_any_hwtask_is_not_locked(self):
        less = self.create_lesson()
        hw = Homework.objects.create(lesson=less, is_mandatory=True)
        HomeworkTask.objects.create(homework=hw, is_under_construction=False, is_mandatory=True, difficulty=1, description=HomeworkTaskDescriptionFactory())
        HomeworkTask.objects.create(homework=hw, is_under_construction=True, is_mandatory=True, difficulty=1, description=HomeworkTaskDescriptionFactory())
        with self.assertRaises(InvalidLockError):
            less.lock_for_construction()

    def test_deserialization(self):
        json = b'{"video_link_1": "www.yt.com/aa", "course": 1,' \
               b'"intro": "Hello", "content": "I aint got much", "annexation": "Yo"}'
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = LessonSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        lesson = serializer.save()

        self.assertEqual(lesson.lesson_number, 1)
        self.assertEqual(lesson.is_under_construction, True)
        self.assertEqual(lesson.video_link_1, "www.yt.com/aa")
        self.assertEqual(lesson.video_link_2, "")
        self.assertEqual(lesson.intro, "Hello")
        self.assertEqual(lesson.content, "I aint got much")
        self.assertEqual(lesson.annexation, "Yo")

    def test_deserialization_works_with_fake_lesson_number_and_construction_fields(self):
        json = b'{"video_link_1": "www.yt.com/aa", "course": 1,' \
               b'"intro": "Hello", "content": "I aint got much", "annexation": "Yo",' \
               b'"lesson_number": 519, "is_under_construction": false}'
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        serializer = LessonSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        lesson = serializer.save()

        self.assertEqual(lesson.lesson_number, 1)
        self.assertEqual(lesson.is_under_construction, True)
        self.assertEqual(lesson.video_link_1, "www.yt.com/aa")
        self.assertEqual(lesson.video_link_2, "")
        self.assertEqual(lesson.intro, "Hello")
        self.assertEqual(lesson.content, "I aint got much")
        self.assertEqual(lesson.annexation, "Yo")
