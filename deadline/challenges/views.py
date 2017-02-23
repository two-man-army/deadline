import json

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from challenges.models import Challenge, Submission, TestCase, ChallengeCategory, SubCategory
from challenges.serializers import ChallengeSerializer, SubmissionSerializer, TestCaseSerializer, ChallengeCategorySerializer, SubCategorySerializer, LimitedChallengeSerializer
from challenges.tasks import run_grader
from challenges.helper import grade_result, update_user_score


# Create your views here.
class ChallengeDetailView(RetrieveAPIView):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = (IsAuthenticated, )


class ChallengeCategoryListView(ListAPIView):
    serializer_class = ChallengeCategorySerializer
    queryset = ChallengeCategory.objects.all()


class SubCategoryDetailView(RetrieveAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = (IsAuthenticated, )


class SubmissionDetailView(RetrieveAPIView):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        """ Get the submission and meanwhile check if its tests have been completed. If they have, save them """
        challenge_pk = kwargs.get('challenge_pk')
        submission_pk = kwargs.get('pk')
        try:
            challenge = Challenge.objects.get(id=challenge_pk)
            try:
                submission = Submission.objects.get(id=submission_pk)
                if submission.challenge_id != challenge.id:
                    return Response(data={'error': 'Submission with ID {} does not belong to Challenge with ID {}'
                                    .format(submission_pk, challenge_pk)},
                                    status=400)

                # Query for the tests and populate if there is a result (AND they were not populated)
                if any(test_case.pending for test_case in submission.testcase_set.all()):
                    potential_result = run_grader.AsyncResult(submission.task_id)
                    if potential_result.ready():
                        results = json.loads(potential_result.get())

                        for idx, test_case in enumerate(submission.testcase_set.all()):
                            test_results = results['results'][idx]

                            test_case.success = test_results['success']
                            test_case.time = test_results['time'] + 's'
                            test_case.pending = False
                            test_case.description = test_results['description']
                            test_case.traceback = test_results['traceback']
                            test_case.error_message = test_results['error_message']
                            test_case.save()  # TODO: Maybe save at once SOMEHOW, django transaction does not work

                        grade_result(submission)  # update the submission's score

                        update_user_score(user=submission.author, submission=submission)
                return super().retrieve(request, *args, **kwargs)
            except Submission.DoesNotExist:
                return Response(data={'error': 'Submission with ID {} does not exist.'.format(submission_pk)},
                                status=400)
        except Challenge.DoesNotExist:
            return Response(data={'error': 'Challenge with ID {} does not exist.'.format(challenge_pk)},
                            status=400)


class SubmissionListView(ListAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk')
        return Response(data=SubmissionSerializer(Submission.objects
                                                  .filter(challenge=challenge_pk, author=request.user)
                                                  .all(), many=True).data
                        , status=200)


class TopSubmissionListView(ListAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk')
        top_submissions = Submission.objects.raw('SELECT id, author_id, max(result_score) as maxscore '
                                                 'FROM challenges_submission '
                                                 'WHERE challenge_id = %s '
                                                 'GROUP BY author_id '
                                                 'ORDER BY maxscore DESC;', params=[challenge_pk])
        return Response(data=SubmissionSerializer(top_submissions, many=True).data)


class LatestAttemptedChallengesListView(ListAPIView):
    """ This view should return the challenges attempted by the user, with the newest coming first """
    serializer_class = LimitedChallengeSerializer
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        latest_submissions = Submission.objects.raw('SELECT * FROM challenges_submission WHERE author_id = %s GROUP BY challenge_id ORDER BY created_at DESC LIMIT 10;', params=[request.user.id])
        latest_challenges = [submission.challenge for submission in latest_submissions]
        return Response(data=LimitedChallengeSerializer(latest_challenges, many=True).data)


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
            submission = Submission(code=code_given, author=User.objects.first(),
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
            test_case = TestCase.objects.get(id=test_case_pk)
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
                                       Submission.objects.filter(  # All test cases who belong to the given submission
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



