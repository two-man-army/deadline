from io import BytesIO

from django.test import TestCase
from rest_framework.parsers import JSONParser

from education.models import Course, Lesson
from education.serializers import LessonSerializer


class CourseModelTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name='tank', difficulty=1)

    def test_creation(self):
        less = Lesson.objects.create(lesson_number=1,
                              video_link_1='youtube.com/tank', course=self.course,
                              intro='Today we will tank',
                              content='Tank much')
        self.course.refresh_from_db()

        self.assertEqual(less.course, self.course)
        self.assertEqual(less.video_link_1, 'youtube.com/tank')
        self.assertEqual(less.annexation, '')
        self.assertEqual(self.course.lessons.count(), 1)
        self.assertEqual(self.course.lessons.first(), less)
        self.assertTrue(less.is_under_construction)

    def test_get_course_returns_course(self):
        received_course = Lesson.objects.create(lesson_number=1,
                              video_link_1='youtube.com/tank', course=self.course,
                              intro='Today we will tank',
                              content='Tank much').get_course()
        self.assertEqual(received_course, self.course)

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
