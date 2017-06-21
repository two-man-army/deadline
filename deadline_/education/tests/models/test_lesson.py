from django.test import TestCase

from education.models import Course, Lesson


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
