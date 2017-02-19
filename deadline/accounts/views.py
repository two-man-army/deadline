from django.shortcuts import render
from django.http import HttpRequest
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from accounts.serializers import UserSerializer
from accounts.models import User
from accounts.helpers import hash_password


@api_view(['POST'])
def register(request: Request):
    """ Register a User"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # attach the unique user token
        response_data = {'user_token': user.auth_token.key}
        response_data.update(serializer.data)

        return Response(data=response_data,
                        status=status.HTTP_201_CREATED)
    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request: Request):
    data = request.data
    error = None

    if 'email' not in data or 'password' not in data:
        error = 'E-mail or password fields were empty!'

    given_email = data['email']
    given_password = data['password']

    user = User.objects.filter(email=given_email).first()
    if user is None:
        error = f'Invalid credentials!'
        return Response(data={'error': error}, status=status.HTTP_400_BAD_REQUEST)

    # Try to validate the password
    hashed_password = hash_password(given_password, user.salt)
    if hashed_password != user.password:
        error = f'Invalid credentials!'

    if error:
        return Response(data={'error': error}, status=status.HTTP_400_BAD_REQUEST)

    response_data = {'user_token': user.auth_token.key}
    response_data.update(UserSerializer(user).data)
    return Response(data=response_data, status=status.HTTP_202_ACCEPTED)


@ensure_csrf_cookie
@api_view(['GET'])
def index(request: Request):
    return Response()