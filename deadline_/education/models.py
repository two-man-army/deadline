from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from challenges.validators import PossibleFloatDigitValidator
from challenges.models import Language, User
from accounts.models import Role


class Course(models.Model):
    name = models.CharField(max_length=200)
    teachers = models.ManyToManyField(to='accounts.User')
    difficulty = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(10), PossibleFloatDigitValidator(['0', '5'])])
    languages = models.ManyToManyField(to='challenges.Language')
    is_under_construction = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        teacher_role = Role.objects.filter(name='Teacher').first()
        # Don't allow teachers that do not have the role Teacher
        for teacher in self.teachers.all():
            if teacher.role != teacher_role:
                raise ValidationError(f'The Teacher of a Course should have the appropriate Teacher role!')


class Lesson(models.Model):
    """
    A single Lesson in a Course
    """

    # represents the number of the lesson in the Course, used for continuation
    # e.g lesson #2 requires lesson #1 to have passed
    lesson_number = models.IntegerField()
    is_under_construction = models.BooleanField(default=True)
    # Links to videos
    video_link_1 = models.CharField(max_length=100, default='')
    video_link_2 = models.CharField(max_length=100, default='')
    video_link_3 = models.CharField(max_length=100, default='')
    video_link_4 = models.CharField(max_length=100, default='')
    video_link_5 = models.CharField(max_length=100, default='')

    course = models.ForeignKey(Course, related_name='lessons')

    intro = models.CharField(max_length=1000)
    content = models.CharField(max_length=3000)
    annexation = models.CharField(max_length=3000)


class Homework(models.Model):
    lesson = models.ForeignKey(Lesson)
    is_mandatory = models.BooleanField()


class HomeworkTask(models.Model):
    homework = models.ForeignKey(Homework)
    test_case_count = models.IntegerField()
    supported_languages = models.ManyToManyField(Language)
    description = models.OneToOneField('HomeworkTaskDescription')
    is_mandatory = models.BooleanField()
    consecutive_number = models.IntegerField(default=0)
    difficulty = models.IntegerField()  # 1-10


class HomeworkTaskDescription(models.Model):
    """ Holds the description for a specific homework task """
    content = models.CharField(max_length=3000, default='')
    input_format = models.CharField(max_length=500, default='')
    output_format = models.CharField(max_length=1000, default='')
    constraints = models.CharField(max_length=1000, default='')
    sample_input = models.CharField(max_length=1000, default='')
    sample_output = models.CharField(max_length=1000, default='')
    explanation = models.CharField(max_length=1000, default='')


class UserLessonProgress(models.Model):
    user = models.ForeignKey(User)
    lesson = models.ForeignKey(Lesson)
    is_complete = models.BooleanField()
    course_progress = models.ForeignKey('UserCourseProgress')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # validate the courses
        course_id = self.course_progress.course_id
        lesson_course_id = self.lesson.course_id
        if course_id != lesson_course_id:
            raise Exception("Inconsistency between CourseProgress' course and Lesson's course")

        # validate the current User and CourseProgress' User
        cp_user_id = self.course_progress.user_id
        if self.user_id != cp_user_id:
            raise Exception("Inconsistency between given User and CourseProgress' user")

        if self.course_progress.course.is_under_construction:
            raise Exception('Cannot create UserLessonProgress while Course is under construction!')

        if self.lesson.is_under_construction:
            raise Exception('Cannot create UserLessonProgress while Lesson is under construction!')

        return super().save(force_insert, force_update, using, update_fields)


class UserCourseProgress(models.Model):
    is_complete = models.BooleanField(default=False)
    user = models.ForeignKey(User)
    course = models.ForeignKey(Course)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        # validate that course and course's lessons are not under construction
        if self.course.is_under_construction:
            raise Exception('Cannot create UserCourseProgress while Course is under construction!')

        if any([lesson.is_under_construction for lesson in self.course.lessons.all()]):
            raise Exception("Cannot create UserCourseProgress while a Course's Lesson is under construction!")

        return super().save(force_insert, force_update, using, update_fields)
