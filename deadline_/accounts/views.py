from datetime import datetime, timedelta

from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.request import Request
from rest_framework import status
from rest_framework.views import APIView

from accounts.serializers import UserSerializer, UserProfileSerializer
from accounts.models import User, Role, UserPersonalDetails
from accounts.helpers import hash_password
from helpers import datetime_now
from challenges.services.submissions import submissions_count_by_date_from_user_since, submissions_count_by_month_from_user_since
from constants import BASE_USER_ROLE_NAME
from decorators import fetch_models


class UserDetailView(RetrieveAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serialized_data = self.get_serializer(instance).data
        serialized_data['follower_count'] = instance.users_followed.count()
        return Response(serialized_data)


# /accounts/{user_id}/profile
class ProfilePageView(RetrieveAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()

    def get_serializer_context(self):
        return {'caller': self.request.user}


class InvalidDateModeException(Exception):
    pass


# /accounts/{user_id}/recent_submissions?date_mode={date_mode}
class UserRecentSubmissionCount(APIView):
    """
    Returns the number of user submissions by dates for X days ago, depending on the date_mode
    Accepts three date modes - weekly, monthly, early

    Sample response:
    {
        "2016-09-28": 3,
        "2016-09-29": 17,
        "2016-09-30": 2,
        "2016-10-01": 9
    }
    """
    permission_classes = (IsAuthenticated, )
    model_classes = (User, )

    @fetch_models
    def get(self, request, user, *args, **kwargs):
        date_mode = request.GET.get('date_mode', None)
        try:
            since_date = self.evaluate_since_date(date_mode)
        except InvalidDateModeException:
            return Response(status=400, data={'error': f'Date mode {date_mode} is not supported!'})

        return Response(status=200, data=self.get_submissions_count(user, date_mode, since_date))

    def evaluate_since_date(self, date_mode):
        if date_mode == 'weekly':
            subtract_delta = timedelta(days=7)
        elif date_mode == 'monthly':
            subtract_delta = timedelta(days=30)
        elif date_mode == 'yearly':
            subtract_delta = timedelta(days=365)
        else:
            raise InvalidDateModeException()

        return datetime_now() - subtract_delta

    def get_submissions_count(self, user, date_mode, since_date):
        if date_mode == 'weekly' or date_mode == 'monthly':
            return submissions_count_by_date_from_user_since(user, since_date)
        elif date_mode == 'yearly':
            return submissions_count_by_month_from_user_since(user, since_date)


@api_view(['POST'])
@permission_classes([])
def register(request: Request):
    """ Register a User"""
    # Set the base role for a user
    user_role = Role.objects.filter(name=BASE_USER_ROLE_NAME).first()
    request.data['role'] = user_role.id
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        UserPersonalDetails.objects.create(user=user, interests=[])

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
