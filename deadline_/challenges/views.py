import json
from datetime import datetime

from django.utils import timezone
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from constants import MIN_SUBMISSION_INTERVAL_SECONDS, GRADER_TEST_RESULTS_RESULTS_KEY, GRADER_COMPILE_FAILURE
from challenges.models import Challenge, Submission, TestCase, MainCategory, SubCategory, Language
from challenges.serializers import ChallengeSerializer, SubmissionSerializer, TestCaseSerializer, MainCategorySerializer, SubCategorySerializer, LimitedChallengeSerializer, LanguageSerializer
from challenges.tasks import run_grader_task
from challenges.helper import grade_result, update_user_score
from challenges.helper import update_test_cases


# /challenges/{challenge_id}
class ChallengeDetailView(RetrieveAPIView):
    """ Returns information about a specific Challenge """
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = (IsAuthenticated, )


# /challenges/latest_attempted
class LatestAttemptedChallengesListView(ListAPIView):
    """
    This view returns the last 10 challenges attempted by the user, with the newest coming first
    """
    serializer_class = LimitedChallengeSerializer
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        latest_submissions = Submission.fetch_last_10_submissions_for_unique_challenges_by_user(
            user_id=request.user.id)

        latest_challenges = [submission.challenge for submission in latest_submissions]

        return Response(data=LimitedChallengeSerializer(latest_challenges, many=True, context={'request': request}).data)


# /challenges/categories/all
class MainCategoryListView(ListAPIView):
    """ Returns information about all Categories """
    serializer_class = MainCategorySerializer
    queryset = MainCategory.objects.all()


# /challenges/subcategories/{subcategory_id}
class SubCategoryDetailView(RetrieveAPIView):
    """ Returns information about a specific SubCategory, like challenges associated to it """
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = (IsAuthenticated, )


# /challenges/{challenge_id}/submissions/new
class SubmissionCreateView(CreateAPIView):
    """
    Creates a new Submission for a specific Challenge
    The test cases are also created and will be populated on next query to VIEW the Submission (once graded)
    """
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk')
        try:
            challenge = Challenge.objects.get(id=challenge_pk)
            code_given = request.data.get('code')
            language_given = request.data.get('language')

            if not code_given:
                return Response(data={'error': 'The code given cannot be empty.'},
                                status=400)
            elif not language_given:
                return Response(data={'error': 'The language given cannot be empty.'},
                                status=400)

            try:
                language = challenge.supported_languages.get(name=language_given)
            except Language.DoesNotExist:
                return Response(data={'error': f'The language {language_given} is not supported!'},
                                status=400)

            # Check for time between submissions
            time_now = timezone.make_aware(datetime.now(), timezone.utc)
            time_since_last_submission = time_now - request.user.last_submit_at
            if time_since_last_submission.seconds < MIN_SUBMISSION_INTERVAL_SECONDS:
                return Response(data={'error': 'You must wait 10 more seconds before submitting a solution.'},
                                status=400)

            import subprocess
            import os

            celery_grader_task = run_grader_task.delay(test_case_count=challenge.test_case_count,
                                                  test_folder_name=challenge.test_file_name,
                                                  code=code_given, lang=language.name)

            submission = Submission(code=code_given, author=request.user,
                                    challenge=challenge, task_id=celery_grader_task,
                                    language=language)
            submission.save()

            request.user.last_submit_at = timezone.now()
            request.user.save()

            # Create the test cases
            TestCase.objects.bulk_create([TestCase(submission=submission) for _ in range(challenge.test_case_count)])

            return Response(data=SubmissionSerializer(submission).data, status=201)
        except Challenge.DoesNotExist:
            return Response(data={'error': 'Challenge with ID {} does not exist.'.format(challenge_pk)},
                            status=400)


# /challenges/{challenge_id}/submissions/{submission_id}
class SubmissionDetailView(RetrieveAPIView):
    """ Returns information about a specific Submission """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        """
        Get the submission,
            validate and
            check if its tests have been completed. If they have, save them
        """
        result = self.validate_data(challenge_pk=kwargs.get('challenge_pk'),
                                    submission_pk=kwargs.get('pk'))
        if isinstance(result, Response):
            return result  # There has been a validation error

        challenge, submission = result

        # Query for the tests and populate if there is a result (AND they were not populated)
        submission_is_pending = any(test_case.pending for test_case in submission.testcase_set.all())
        if submission_is_pending:
            potential_result = run_grader_task.AsyncResult(submission.task_id)
            if potential_result.ready():
                result = potential_result.get()

                if GRADER_COMPILE_FAILURE in result:
                    # Compiling the code has failed
                    submission.compiled = False
                    submission.pending = False
                    submission.compile_error_message = result[GRADER_COMPILE_FAILURE]
                    submission.save()
                    return super().retrieve(request, *args, **kwargs)

                overall_results = result

                # Update the Submission's TestCases
                update_test_cases(grader_results=overall_results[GRADER_TEST_RESULTS_RESULTS_KEY],
                                  test_cases=submission.testcase_set.all())

                grade_result(submission)  # update the submission's score

                update_user_score(user=submission.author, submission=submission)

        return super().retrieve(request, *args, **kwargs)

    def validate_data(self, challenge_pk, submission_pk) -> Response or tuple():
        """ Validate the given challenge_id, submission_id and their association """
        try:
            challenge = Challenge.objects.get(id=challenge_pk)
        except Challenge.DoesNotExist:
            return Response(data={'error': 'Challenge with ID {} does not exist.'.format(challenge_pk)},
                            status=400)
        try:
            submission = Submission.objects.get(id=submission_pk)
        except Submission.DoesNotExist:
            return Response(data={'error': 'Submission with ID {} does not exist.'.format(submission_pk)},
                            status=400)

        if submission.challenge_id != challenge.id:
            return Response(data={'error': 'Submission with ID {} does not belong to Challenge with ID {}'
                            .format(submission_pk, challenge_pk)},
                            status=400)

        # validate that the current User is either the author or has solved it perfectly
        if submission.author_id != self.request.user.id:
            top_user_submission = Submission.fetch_top_submission_for_challenge_and_user(challenge.id, self.request.user.id)
            if top_user_submission is None or top_user_submission.result_score != challenge.score:
                # User has not fully solved this and as such does not have access to the solution
                return Response(data={'error': 'You have not fully solved the challenge'}, status=401)

        return challenge, submission


# /challenges/{challenge_id}/submissions/all
class SubmissionListView(ListAPIView):
    """ Returns all the Submissions for a specific Challenge from the current user """
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk')
        return Response(data=SubmissionSerializer(Submission.objects
                                                  .filter(challenge=challenge_pk, author=request.user)
                                                  .order_by('-created_at')  # newest first
                                                  .all(), many=True).data
                        , status=200)


# /challenges/{challenge_id}/submissions/top
class TopSubmissionListView(ListAPIView):
    """
    Returns the top-rated Submissions for a specific Challenge, one for each User
     Used for a Challenge's leaderboard
    """
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk', '')
        try:
            Challenge.objects.get(pk=challenge_pk)
        except Challenge.DoesNotExist:
            return Response(data={'error': f'Invalid challenge id {challenge_pk}!'}, status=400)

        top_submissions = Submission.fetch_top_submissions_for_challenge(challenge_id=challenge_pk)

        return Response(data=SubmissionSerializer(top_submissions, many=True).data)


# /challenges/{challenge_id}/submissions/selfTop
class SelfTopSubmissionDetailView(RetrieveAPIView):
    """
    Returns the top-rated submission for the current User
    """
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk', '')
        try:
            Challenge.objects.get(pk=challenge_pk)
        except Challenge.DoesNotExist:
            return Response(data={'error': f'Invalid challenge id {challenge_pk}!'}, status=400)

        top_submission = Submission.fetch_top_submission_for_challenge_and_user(challenge_id=challenge_pk, user_id=request.user.id)

        if top_submission is None:
            return Response(status=404)  # doesnt exist

        return Response(data=SubmissionSerializer(top_submission).data)


# /challenges/languages/{language_name}
class LanguageDetailView(RetrieveAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = (IsAuthenticated, )
    lookup_field = 'name'

    def retrieve(self, request, *args, **kwargs):
        self.kwargs['name'] = kwargs.get('name', '').capitalize()
        return super().retrieve(request, *args, **kwargs)


# /challenges/{challenge_id}/submissions/{submission_id}/test/{testcase_id}
class TestCaseDetailView(RetrieveAPIView):
    """ Returns information about a specific TestCase """
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


# /challenges/{challenge_id}/submissions/{submission_id}/tests
class TestCaseListView(ListAPIView):
    """ Returns all the TestCases for a specific Submission on a specific Challenge"""
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
