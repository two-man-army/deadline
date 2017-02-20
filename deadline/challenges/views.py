from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView

from challenges.models import Challenge, Submission
from challenges.serializers import ChallengeSerializer, SubmissionSerializer


# Create your views here.
class ChallengeDetailView(RetrieveAPIView):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer


class SubmissionDetailView(RetrieveAPIView):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
