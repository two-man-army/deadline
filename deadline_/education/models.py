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