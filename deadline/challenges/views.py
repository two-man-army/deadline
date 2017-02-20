from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from challenges.models import Challenge, Submission, TestCase
from challenges.serializers import ChallengeSerializer, SubmissionSerializer, TestCaseSerializer
from challenges.tasks import run_grader


# Create your views here.
class ChallengeDetailView(RetrieveAPIView):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = (IsAuthenticated, )


class SubmissionDetailView(RetrieveAPIView):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, )


class SubmissionCreateView(CreateAPIView):
    """
    Creates a submission, given code by the user.
    The test cases are also created and will be populated on next query to view the submission
    """
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk')
        try:
            challenge = Challenge.objects.get(id=challenge_pk)
            code_given = request.data.get('code')
            if not code_given:
                return Response(data={'error': 'The code given cannot be empty.'.format(challenge_pk)},
                                status=400)
            celery_grader_task = run_grader.delay(challenge.test_file_name, code_given)
            submission: Submission = Submission(code=code_given, author=request.user,
                                                challenge=challenge, task_id=celery_grader_task.id)
            submission.save()
            # Create the test cases
            TestCase.objects.bulk_create([TestCase(submission=submission) for _ in range(challenge.test_case_count)])

            return Response(data=SubmissionSerializer(submission).data, status=201)
        except Challenge.DoesNotExist:
            return Response(data={'error': 'Challenge with ID {} does not exist.'.format(challenge_pk)},
                            status=400)


class TestCaseDetailView(RetrieveAPIView):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = (IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        # Validate the challenge and submission id
        test_case_pk = kwargs.get('pk')
        submission_pk = kwargs.get('submission_pk')
        challenge_pk = kwargs.get('challenge_pk')
        try:
            test_case: TestCase = TestCase.objects.get(id=test_case_pk)
            if test_case.submission_id != int(submission_pk):
                return Response(data={'error': 'Invalid submission for the specific test case!'}, status=400)
            elif test_case.submission.challenge_id != int(challenge_pk):
                return Response(data={'error': 'Invalid challenge for the specific test case!'}, status=400)
        except TestCase.DoesNotExist:
            pass

        return super().retrieve(request, *args, **kwargs)


class TestCaseListView(ListAPIView):
    serializer_class = TestCaseSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        challenge_pk = self.kwargs.get('challenge_pk')
        submission_pk = self.kwargs.get('submission_pk')

        return TestCase.objects.filter(submission=
                                       Submission.objects.filter(  # All submissions who belong to the given challenge
                                           id=submission_pk,
                                           challenge=Challenge.objects.filter(id=challenge_pk).first())
                                       .first())

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        # Attach an error
        if not response.data:
            return Response(
                data={'error': 'No testcases were found, the given challenge or submission ID is most likely invalid'},
                status=400)

        return response
