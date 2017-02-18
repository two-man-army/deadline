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


@ensure_csrf_cookie
@api_view(['GET'])
def index(request: Request):
    return Response()