from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from challenges.validators import PossibleFloatDigitValidator
from challenges.models import Language
from accounts.models import Role


class Course(models.Model):
    name = models.CharField(max_length=200)
    teachers = models.ManyToManyField(to='accounts.User')
    difficulty = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(10), PossibleFloatDigitValidator(['0', '5'])])
    languages = models.ManyToManyField(to='challenges.Language')

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
    # TODO: homework = models.foreignKey(Homework)


class Homework(models.Model):
    pass


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
