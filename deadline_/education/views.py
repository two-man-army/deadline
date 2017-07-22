from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from challenges.models import Language
from challenges.tasks import run_homework_grader_task
from decorators import fetch_models, enforce_forbidden_fields
from education.permissions import IsTeacher, IsEnrolledOnCourseOrIsTeacher, IsTeacherOfCourse
from education.serializers import CourseSerializer, HomeworkTaskSerializer, LessonSerializer, TaskSubmissionSerializer
from education.models import Course, Lesson, HomeworkTask, HomeworkTaskTest, Homework
from education.helpers import create_task_test_files
from errors import FetchError
from helpers import fetch_models_by_pks
from views import BaseManageView





