import os
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

from constants import EDUCATION_TEST_FILES_FOLDER
from education.errors import StudentAlreadyEnrolledError, InvalidEnrollmentError, InvalidLockError, AlreadyLockedError
from challenges.validators import PossibleFloatDigitValidator
from challenges.models import Language, User
from accounts.models import Role


class Course(models.Model):
    name = models.CharField(max_length=200)
    teachers = models.ManyToManyField(to='accounts.User', related_name='courses')
    main_teacher = models.ForeignKey(User)
    difficulty = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(10), PossibleFloatDigitValidator(['0', '5'])])
    languages = models.ManyToManyField(to='challenges.Language')
    is_under_construction = models.BooleanField(default=True)
    students = models.ManyToManyField(User, through='UserCourseProgress', related_name='enrolled_courses')

    def clean(self):
        super().clean()
        teacher_role = Role.objects.filter(name='Teacher').first()
        # Don't allow teachers that do not have the role Teacher
        for teacher in self.teachers.all():
            if teacher.role != teacher_role:
                raise ValidationError(f'The Teacher of a Course should have the appropriate Teacher role!')

    def enroll_student(self, student: User):
        if self.is_under_construction:
            raise InvalidEnrollmentError('Cannot enroll a student while the course is under construction!')
        if self.has_student(student):
            raise StudentAlreadyEnrolledError()
        # create a UserCourseProgress for the new student
        ucp = UserCourseProgress.objects.create(user=student, course=self, is_complete=False)
        # create a UserLessonProgress for each lesson
        for lesson in self.lessons.all():
            UserLessonProgress.objects.create(user=student, lesson=lesson, course_progress=ucp, is_complete=False)

    def has_teacher(self, us: User):
        return any(us.id == tch.id for tch in self.teachers.all())

    def has_student(self, us: User):
        return any(us.id == st.id for st in self.students.all())

    def is_main_teacher(self, us: User):
        return self.main_teacher_id == us.id

    def can_lock(self):
        """
            Returns true/false if the Course is available for locking
            A course can only be locked if all of its lessons are locked
        """
        for less in self.lessons.all():
            if less.is_under_construction:
                return False
        return True

    def lock_for_construction(self):
        """
        'Locks' the Course, meaning no important information can be modified anymore.
        In the case of the Course model, this impacts everything below it.
        Once a Course is locked, you can no longer create more Lessons (and as all the lessons are locked, further limitations are in place),
            you cannot edit anything

        For a Course to be locked, all Lessons must all be locked as well
        """
        if not self.is_under_construction:
            raise AlreadyLockedError('Course is already locked.')

        if not self.can_lock():
            raise InvalidLockError('Cannot lock a Course while a Lesson is under construction!')
        self.is_under_construction = False
        self.save()

    def remove_lesson(self, lesson):
        """
        Removes a Lesson from the Course's lessons
        """
        if lesson.course_id != self.id:
            raise Exception(f'Lesson {lesson.id} does not belong to course {self.id}')

        lesson.course_id = -1  # don't delete it, just make it invalid
        lesson.save()
        # fix the ordering of the other lessons
        for old_lesson in self.lessons.all():
            if old_lesson.lesson_number > lesson.lesson_number:
                old_lesson.lesson_number -= 1
                old_lesson.save()


@receiver(post_save, sender=Course)
def course_post_save(sender, instance: Course, created, *args, **kwargs):
    """
        Add the main teacher to the teachers of the course
    """
    if created:
        instance.teachers.add(instance.main_teacher)


class Lesson(models.Model):
    """
    A single Lesson in a Course
    """
    # TODO: Add Name parameter
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

    def get_course(self) -> Course:
        return self.course

    def can_lock(self) -> (bool, str):
        """ Returns true/false if the Lesson is available for locking and a message of why its not"""
        if not self.is_under_construction:
            return False, 'Cannot lock an already locked Lesson'

        for hw in self.homework_set.all():
            for task in hw.homeworktask_set.all():
                if task.is_under_construction:
                    return False, 'Cannot lock the Lesson while a HomeworkTask is under construction'
        return True, ''

    def lock_for_construction(self):
        """
        'Locks' the Lesson, meaning no important information can be modified anymore.
        In the case of the Lesson model, this impacts everything below it.
        Once a Lesson is locked, Homework and Homework tasks cannot be created any more.

        For a Lesson to be locked, all HomeworkTasks must all be locked as well
        """
        if not self.is_under_construction:
            raise AlreadyLockedError('Lesson is already locked.')

        can_lock, err_msg = self.can_lock()
        if not can_lock:
            raise InvalidLockError(err_msg)
        self.is_under_construction = False
        self.save()

    def is_completed_by(self, user: 'User') -> bool:
        """
        Returns a boolean, indicating if the Lesson is completed by the given user
        """
        user_lesson_progress = UserLessonProgress.objects.filter(user_id=user.id).first()
        if user_lesson_progress is None:
            return False
        return user_lesson_progress.is_complete


class Homework(models.Model):
    lesson = models.ForeignKey(Lesson)
    is_mandatory = models.BooleanField()

    def get_course(self):
        return self.lesson.get_course()

    def remove_task(self, task):
        """
        Removes a HomeworkTask from this Homework
        """
        if task not in self.homeworktask_set.all():
            raise Exception(f'HomeworkTask {task.id} does not belong to Homework {self.id}')

        task.homework_id = -1
        task.save()

        # fix the ordering of the other tasks
        for old_task in self.homeworktask_set.all():
            if old_task.consecutive_number > task.consecutive_number:
                old_task.consecutive_number -= 1
                old_task.save()


class HomeworkTask(models.Model):
    # TODO: Add some sort of requirement for Teacher to add an original solution and have him maintain it working
    homework = models.ForeignKey(Homework)
    test_case_count = models.IntegerField(default=0)
    supported_languages = models.ManyToManyField(Language)
    description = models.OneToOneField('HomeworkTaskDescription')
    is_mandatory = models.BooleanField()
    is_under_construction = models.BooleanField(default=True)
    consecutive_number = models.IntegerField(default=0)
    difficulty = models.IntegerField()  # 1-10

    def get_course(self):
        return self.homework.get_course()

    def get_absolute_test_files_path(self):
        """
        Returns the absolute path to the input/output files for the given Task
         e.g - /education_tests/{course_name}/{lesson_number}/{task_number}/
        """
        course_name = self.homework.lesson.course.name
        task_number = self.consecutive_number
        lesson_number = self.homework.lesson.lesson_number

        task_tests_dir = os.path.join(
            os.path.join(
                os.path.join(EDUCATION_TEST_FILES_FOLDER, course_name),
                str(lesson_number)
            ),
            str(task_number),
        )

        return task_tests_dir

    def lock_for_construction(self):
        self.is_under_construction = False
        self.save()


class HomeworkTaskDescription(models.Model):
    """ Holds the description for a specific homework task """
    content = models.CharField(max_length=3000, default='')
    input_format = models.CharField(max_length=500, default='')
    output_format = models.CharField(max_length=1000, default='')
    constraints = models.CharField(max_length=1000, default='')
    sample_input = models.CharField(max_length=1000, default='')
    sample_output = models.CharField(max_length=1000, default='')
    explanation = models.CharField(max_length=1000, default='')


class HomeworkTaskTest(models.Model):
    task = models.ForeignKey(HomeworkTask)
    input_file_path = models.CharField(max_length=150)
    output_file_path = models.CharField(max_length=150)
    consecutive_number = models.IntegerField()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        created = self.pk is None
        if created:
            self.consecutive_number = self.task.homeworktasktest_set.count() + 1

        return super().save(force_insert, force_update, using, update_fields)

    def consecutiveness_is_valid(self):
        return self.consecutive_number == self.task.homeworktasktest_set.count() + 1


@receiver(post_save, sender=HomeworkTaskTest)
def hw_task_test_post_save(sender, instance: HomeworkTaskTest, created, *args, **kwargs):
    """
        Increment the task's test_case_count
    """
    if created:
        instance.task.test_case_count += 1
        instance.task.save()


class TaskSubmission(models.Model):
    """
    A user's submission for a given HomeworkTask
    """
    task = models.ForeignKey(HomeworkTask)
    author = models.ForeignKey(User)
    code = models.CharField(max_length=4000, blank=False)
    celery_task_id = models.CharField(max_length=100, blank=False)  # FIXME: Unused?
    is_solved = models.BooleanField(default=False)
    grading_is_pending = models.BooleanField(default=True)
    has_compiled = models.BooleanField(default=True)
    compile_error_message = models.CharField(max_length=1000, blank=False)
    language = models.ForeignKey(Language, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    timed_out = models.BooleanField(default=False)  # shows if any test failed for timeout rather than wrong answer


class TaskTestCase(models.Model):
    submission = models.ForeignKey(TaskSubmission)
    time = models.FloatField(default=0)
    success = models.BooleanField(default=False)
    pending = models.BooleanField(default=True)
    description = models.CharField(max_length=1000)
    traceback = models.CharField(max_length=2000)
    error_message = models.CharField(max_length=100)
    timed_out = models.BooleanField(default=False)


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
    course = models.ForeignKey(Course, related_name='student_progresses')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        # validate that course and course's lessons are not under construction
        if self.course.is_under_construction:
            raise Exception('Cannot create UserCourseProgress while Course is under construction!')

        if any([lesson.is_under_construction for lesson in self.course.lessons.all()]):
            raise Exception("Cannot create UserCourseProgress while a Course's Lesson is under construction!")

        return super().save(force_insert, force_update, using, update_fields)
