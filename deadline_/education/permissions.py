from rest_framework.permissions import BasePermission

from constants import TEACHER_ROLE_NAME
from education.models import Course


class IsTeacher(BasePermission):
    """
    Allows access only to Teachers.
    """

    def has_permission(self, request, view):
        return request.user.role.name == TEACHER_ROLE_NAME


class IsTeacherOfCourse(BasePermission):
    """
        Permissions that allows only people that are teachers of the associated Course
        """
    @staticmethod
    def can_access(course, user):
        return course.has_teacher(user)

    def has_object_permission(self, request, view, obj):
        course = obj if isinstance(obj, Course) else obj.get_course()
        return self.can_access(course, request.user)


class IsEnrolledOnCourseOrIsTeacher(BasePermission):
    """
    Permissions that allows only people that are allowed on the associated course (or are teachers of it)
        access the information
    """

    @staticmethod
    def can_access(course, user):
        return course.has_teacher(user) or course.has_student(user)

    def has_object_permission(self, request, view, obj):
        course = obj if isinstance(obj, Course) else obj.get_course()
        return self.can_access(course, request.user)
