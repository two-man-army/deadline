import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models import User


def follow_decorator(view_func, *args, **kwargs):
    def _follow(request, *args, **kwargs):
        if 'target' not in request.GET:
            return Response(status=400, data={'error': f'Follow target missing'})
        if not re.fullmatch(r'^\d+$', request.GET['target']):
            return Response(status=400, data={'error': f'Target querystring must be an integer!'})

        target_user_id = request.GET['target']
        try:
            user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response(status=404)

        return view_func(request, user, *args, **kwargs)
    return _follow


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@follow_decorator
def follow(request: Request, user: User):
    if user in request.user.users_followed.all():
        return Response(status=400, data={'error': f'You have already followed user {user.username}'})

    request.user.follow(user)
    return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@follow_decorator
def unfollow(request: Request, user: User):
    if user not in request.user.users_followed.all():
        return Response(status=400, data={'error': f'You have not followed user {user.username}'})

    request.user.unfollow(user)
    return Response(status=204)
