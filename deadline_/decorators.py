"""
Function/class decorators used across apps
"""
import collections
from rest_framework.response import Response

from helpers import fetch_models_by_pks
from errors import FetchError


def fetch_models(response_function, *args, **kwargs):
    """
    This is a decorator for a ClassView's response method (i.e GET, POST, etc).
    It fetches the Model instances using the given primary keys in the URL.
    If a model fetch fails, it outright returns a 404 response with the given error message
    If it succeeds, it sends the objects as parameters in the function

    Requires the ClassView to have defined:
        model_classes: iterable - the Django ORM classes we'll fetch in the EXACT order that the PKs are in the URL
            example: given the url /course/{course_id}/lesson/{lesson_id} - model_classes MUST be [Course, Lesson],
                otherwise it might fetch the lesson via the course_id.
    Optional in the ClassView:
        main_class: a class - specifies the main class of the view. Given this, this decorator will check all
            the permission_classes for a has_object_permissions method and call it.
            This is done to check for permissions easily.
             If it does not have the permission, the decorator outright returns a 403 Response
    """

    def view_decorator(class_view, *args, **kwargs):
        nonlocal response_function
        request = args[0]
        args = args[1:]  # remove the request object
        if not hasattr(class_view, 'model_classes') and not isinstance(class_view.model_classes, collections.Iterable):
            raise Exception(f'Class {class_view} should have the model_classes iterable variable defined!')
        if len(class_view.model_classes) != len(kwargs.keys()):
            raise Exception(f'Class {class_view} does not have enough classes defined in the model_classes!')

        try:
            models = fetch_models_by_pks({model: model_pk for model, model_pk in zip(class_view.model_classes, kwargs.values())})
            if hasattr(class_view, 'main_class') and hasattr(class_view, 'permission_classes'):
                main_obj = [model for model in models if isinstance(model, class_view.main_class)][0]
                for PermissionClass in [permission for permission in class_view.permission_classes
                                   if hasattr(permission, 'has_object_permission')]:
                    if not PermissionClass().has_object_permission(request, class_view, main_obj):
                        return Response(status=403)

            return response_function(class_view, request, *(list(models) + list(args)), **kwargs)
        except FetchError as e:
            return Response(status=404, data={'error': str(e)})

    return view_decorator
