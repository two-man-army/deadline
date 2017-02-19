from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView

from challenges.models import Challenge
from challenges.serializers import ChallengeSerializer


# Create your views here.
class ChallengeDetailView(RetrieveAPIView):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
