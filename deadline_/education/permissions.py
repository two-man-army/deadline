from rest_framework.permissions import BasePermission

from constants import TEACHER_ROLE_NAME


class IsTeacher(BasePermission):
    """
    Allows access only to Teachers.
    """

    def has_permission(self, request, view):
        return request.user.role.name == TEACHER_ROLE_NAME


class IsEnrolledOnCourseOrIsTeacher(BasePermission):
    """
    Permissions that allows only people that are allowed on the associated course (or are teachers of it)
        access the information
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        course = obj.get_course()
        return course.has_teacher(request.user) or course.has_student(request.user)
