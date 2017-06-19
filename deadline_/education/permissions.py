from rest_framework.permissions import BasePermission

from constants import TEACHER_ROLE_NAME


class IsTeacher(BasePermission):
    """
    Allows access only to Teachers.
    """

    def has_permission(self, request, view):
        return request.user.role.name == TEACHER_ROLE_NAME
