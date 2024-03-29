import re

from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.request import Request
from rest_framework import status

from accounts.serializers import UserSerializer
from accounts.models import User, Role
from accounts.helpers import hash_password
from constants import BASE_USER_ROLE_NAME


class UserDetailView(RetrieveAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serialized_data = self.get_serializer(instance).data
        serialized_data['follower_count'] = instance.users_followed.count()
        return Response(serialized_data)

@api_view(['POST'])
@permission_classes([])
def register(request: Request):
    """ Register a User"""
    # Set the base role for a user
    user_role = Role.objects.filter(name=BASE_USER_ROLE_NAME).first()
    request_data = request.data.copy()
    request_data['role'] = user_role.id
    serializer = UserSerializer(data=request_data)
    if serializer.is_valid():
        user = serializer.save()

        # attach the unique user token
        response_data = {'user_token': user.auth_token.key}
        response_data.update(serializer.data)

        return Response(data=response_data,
                        status=status.HTTP_201_CREATED)
    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def login(request: Request):
    data = request.data
    error = None

    if 'email' not in data or 'password' not in data:
        error = 'E-mail or password fields were empty!'
        return Response(data={'error': error}, status=status.HTTP_400_BAD_REQUEST)

    given_email = data['email']
    given_password = data['password']

    user = User.objects.filter(email=given_email).first()
    if user is None:
        error = 'Invalid credentials!'
        return Response(data={'error': error}, status=status.HTTP_400_BAD_REQUEST)

    # Try to validate the password
    hashed_password = hash_password(given_password, user.salt)
    if hashed_password != user.password:
        error = 'Invalid credentials!'

    if error:
        return Response(data={'error': error}, status=status.HTTP_400_BAD_REQUEST)

    response_data = {'user_token': user.auth_token.key}
    response_data.update(UserSerializer(user).data)
    return Response(data=response_data, status=status.HTTP_202_ACCEPTED)


@ensure_csrf_cookie
@permission_classes([])
@api_view(['GET'])
def index(request: Request):
    return Response()
