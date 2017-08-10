import json
from datetime import datetime

from django.utils import timezone
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from constants import MIN_SUBMISSION_INTERVAL_SECONDS
from challenges.models import Challenge, Submission, TestCase, MainCategory, SubCategory, Language, SubmissionVote
from challenges.serializers import ChallengeSerializer, SubmissionSerializer, TestCaseSerializer, MainCategorySerializer, SubCategorySerializer, LimitedChallengeSerializer, LanguageSerializer, LimitedSubmissionSerializer
from challenges.tasks import run_grader_task


# /challenges/{challenge_id}
from decorators import fetch_models
from views import BaseManageView


class ChallengeDetailView(RetrieveAPIView):
    """ Returns information about a specific Challenge """
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = (IsAuthenticated, )


# POST /challenges/{challenge_id}/comments
class ChallengeCommentCreateView(APIView):
    permission_classes = (IsAuthenticated, )
    model_classes = (Challenge, )

    @fetch_models
    def post(self, request, challenge: Challenge, *args, **kwargs):
        comment_content = request.data.get('content', None)
        if not isinstance(comment_content, str):
            return Response(status=400, data={'error': 'Invalid comment content!'})
        if len(comment_content) < 5 or len(comment_content) > 500:
            return Response(status=400, data={'error': 'Comment must be between 5 and 500 characters!'})

        challenge.add_comment(author=request.user, content=comment_content)
        return Response(status=201)


# /challenges/{challenge_id}/comments
class ChallengeCommentManageView(BaseManageView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'POST': ChallengeCommentCreateView.as_view
    }


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
    lookup_field = 'name'


# /challenges/{challenge_id}/submissions/new
class SubmissionCreateView(CreateAPIView):
    """
    Creates a new Submission for a specific Challenge
    The test cases are also created and will be populated on next query to VIEW the Submission (once graded)
    """
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk')
        code_given = request.data.get('code')
        language_given = request.data.get('language')

        challenge, language, is_valid, response = self.validate_data(challenge_pk, code_given, language_given, request.user)
        if not is_valid:
            return response  # invalid data

        submission = Submission(code=code_given, author=request.user, challenge=challenge, task_id=1, language=language)
        submission.save()
        celery_task = run_grader_task.delay(test_case_count=challenge.test_case_count,
                                            test_folder_name=challenge.test_file_name,
                                            code=code_given, lang=language.name, submission_id=submission.id)

        request.user.last_submit_at = timezone.now()
        request.user.save()

        submission.task_id = celery_task
        submission.save()

        # Create the test cases
        TestCase.objects.bulk_create([TestCase(submission=submission) for _ in range(challenge.test_case_count)])

        return Response(data=SubmissionSerializer(submission).data, status=201)

    def validate_data(self, challenge_pk, code_given, language_given, user) -> (Challenge, Language, bool, Response):
        """
        Tries to validate all our data, returning relevant info and a boolean indicating if we validated it
        If it validates it successfully, returns the challenge and language we expect to use
        Otherwise, it returns a response at the end
        """
        try:
            challenge = Challenge.objects.get(id=challenge_pk)
        except Challenge.DoesNotExist:
            return None, None, False, Response(data={'error': 'Challenge with ID {} does not exist.'.format(challenge_pk)},
                                               status=400)

        if not code_given:
            return None, None, False, Response(data={'error': 'The code given cannot be empty.'},
                                             status=400)
        elif not language_given:
            return None, None, False, Response(data={'error': 'The language given cannot be empty.'},
                                               status=400)

        try:
            language = challenge.supported_languages.get(name=language_given)
        except Language.DoesNotExist:
            return None, None, False, Response(data={'error': f'The language {language_given} is not supported!'},
                                               status=400)

        # Check for time between submissions
        time_now = timezone.make_aware(datetime.now(), timezone.utc)
        time_since_last_submission = time_now - user.last_submit_at
        if time_since_last_submission.seconds < MIN_SUBMISSION_INTERVAL_SECONDS:
            resp = Response(data={'error': f'You must wait {MIN_SUBMISSION_INTERVAL_SECONDS} more seconds before submitting a solution.'}, status=400)
            return None, None, False, resp

        return challenge, language, True, None


# /challenges/{challenge_id}/submissions/{submission_id}
class SubmissionDetailView(RetrieveAPIView):
    """
    Returns information about a specific Submission
     Normally used for when we want to open a page with the solution's code
        We want to give access to this submission only if:
            a) the requester is the author of the submission
            b) the requester has solved the associated challenge with max score
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        """
        Get the submission
        """
        result = self.validate_data(challenge_pk=kwargs.get('challenge_pk'),
                                    submission_pk=kwargs.get('pk'))
        if isinstance(result, Response):
            return result  # There has been a validation error
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
    serializer_class = LimitedSubmissionSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk')
        return Response(data=LimitedSubmissionSerializer(Submission.objects
                                                         .filter(challenge=challenge_pk, author=request.user)
                                                         .order_by('-created_at')  # newest first
                                                         .all(), many=True).data)


# POST /challenges/{challenge_id}/submissions/{submission_id}/comments
class SubmissionCommentCreateView(APIView):
    permission_classes = (IsAuthenticated, )
    model_classes = (Challenge, Submission)

    @fetch_models
    def post(self, request, challenge: Challenge, submission: Submission, *args, **kwargs):
        comment_content = request.data.get('content', None)
        result = self.validate_data(current_user=request.user,
                                    comment_content=comment_content,
                                    challenge=challenge, submission=submission)
        if isinstance(result, Response):
            return result  # validation error

        submission.add_comment(author=request.user, content=comment_content)
        return Response(status=201)

    def validate_data(self, current_user, comment_content, challenge, submission):
        """
        Validate that the comment content is OK and that the

            a) the user is the author of the submission
            b) the user has solved the associated challenge with max score
        """
        if not isinstance(comment_content, str):
            return Response(status=400, data={'error': 'Invalid comment content!'})
        if len(comment_content) < 5 or len(comment_content) > 500:
            return Response(status=400, data={'error': 'Comment must be between 5 and 500 characters!'})

        if submission.challenge_id != challenge.id:
            return Response(
                status=400,
                data={'error':
                      f'Submission with ID {submission.id} does not belong to Challenge with ID {challenge.id}'}
            )

        # validate that the current User is either the author or has solved it perfectly
        if submission.author_id != current_user.id:
            top_user_submission = Submission.fetch_top_submission_for_challenge_and_user(challenge.id, current_user.id)
            if top_user_submission is None or top_user_submission.result_score != challenge.score:
                # User has not fully solved this and as such does not have access to the solution
                return Response(data={'error': 'You have not fully solved the challenge'}, status=401)


# /challenges/{challenge_id}/submissions/{submission_id}/comments
class SubmissionCommentManageView(BaseManageView):
    """
        Manages different request methods for the given URL, sending them to the appropriate view class
    """
    VIEWS_BY_METHOD = {
        'POST': SubmissionCommentCreateView.as_view
    }


# /challenges/submissions/{submission_id}/vote
class CastSubmissionVoteView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        is_upvote = request.data.get('is_upvote', None)
        if is_upvote is None:
            return Response(status=400)

        # get the submission
        submission_id = kwargs.get('submission_id', None)
        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response(status=404, data={'error': f'A submission with ID {submission_id} does not exist!'})

        if submission.author_id == self.request.user.id:
            return Response(status=400, data={'error': 'You cannot vote on your own submission!'})

        # try to find such a SubmissionVote first
        submission_vote: SubmissionVote = SubmissionVote.objects.filter(author=self.request.user, submission=submission).first()
        if submission_vote is None:
            # user has not voted before
            SubmissionVote.objects.create(author_id=request.user.id, submission_id=submission.id, is_upvote=is_upvote)
        elif submission_vote.is_upvote != is_upvote:
            # user has voted with another value, update the vote
            submission_vote.is_upvote = is_upvote
            submission_vote.save()

        return Response(status=201)


# TODO: Move delete to the above url :)
# /challenges/submissions/{submission_id}/removeVote
class RemoveSubmissionVoteView(APIView):
    permission_classes = (IsAuthenticated, )

    def delete(self, request, *args, **kwargs):
        # get the submission
        submission_id = kwargs.get('submission_id', None)
        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response(status=404, data={'error': f'A submission with ID {submission_id} does not exist!'})

        if submission.author_id == self.request.user.id:   # ...wtf?
            return Response(status=400, data={'error': 'You cannot vote on your own submission!'})

        # see if such a Submission exists
        submission_vote: SubmissionVote = SubmissionVote.objects.filter(author=self.request.user,
                                                                        submission=submission).first()
        if submission_vote is None:
            return Response(status=404, data={'error': f'The user has not voted for submission with ID {submission.id}'})

        submission_vote.delete()

        return Response(status=200)


# /challenges/{challenge_id}/submissions/top
class TopSubmissionListView(ListAPIView):
    """
    Returns the top-rated Submissions for a specific Challenge, one for each User
     Used for a Challenge's leaderboard
    """
    serializer_class = LimitedSubmissionSerializer
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        challenge_pk = kwargs.get('challenge_pk', '')
        try:
            Challenge.objects.get(pk=challenge_pk)
        except Challenge.DoesNotExist:
            return Response(data={'error': f'Invalid challenge id {challenge_pk}!'}, status=400)

        top_submissions = Submission.fetch_top_submissions_for_challenge(challenge_id=challenge_pk)

        return Response(data=LimitedSubmissionSerializer(top_submissions, many=True).data)


# /challenges/{challenge_id}/submissions/selfTop
class SelfTopSubmissionDetailView(RetrieveAPIView):
    """
    Returns the top-rated submission for the current User
    """
    serializer_class = LimitedSubmissionSerializer
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

        return Response(data=LimitedSubmissionSerializer(top_submission).data)


# /challenges/selfLeaderboardPosition/
class SelfGetLeaderboardPositionView(APIView):
    """
    Returns the current user's position in the overall challenge leaderboard
        and the total amount of users in the leaderboard
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        leaderboard_position = request.user.fetch_overall_leaderboard_position()
        overall_leaderboard_count = request.user.fetch_user_count()

        return Response(data={'position': leaderboard_position, 'leaderboard_count': overall_leaderboard_count})


# /challenges/languages/{language_name}
class LanguageDetailView(RetrieveAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = (IsAuthenticated, )
    lookup_field = 'name'

    def retrieve(self, request, *args, **kwargs):
        self.kwargs['name'] = kwargs.get('name', '').capitalize()
        return super().retrieve(request, *args, **kwargs)


# GET /challenges/languages
class LanguageListView(ListAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = (IsAuthenticated, )


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


class GetLeaderboardView(APIView):
    """
    Returns the overall leaderboard, returning a list of objects containing the user's name and position
    [
        {
            'name':"Nether",
            'position': 1,
            'score': 150
        },
        {
            'name':"Else",
            'position': 2,
            'score': 140
        }
    ]
    """
    def get(self, request, *args, **kwargs):
        # Iterate through all the users and attach their position
        # This will be incredibly slow
        all_users = User.objects.order_by('-score').all()
        last_score = all_users[0].score
        current_position = 1
        user_count = 1
        leaderboard = [{
            'name': all_users[0].username,
            'score': last_score,
            'position': current_position
        }]

        for user in all_users[1:]:
            if user.score != last_score:
                # Found new lower score, lower the current position
                current_position = user_count + 1
                last_score = user.score
            leaderboard.append({
                'name': user.username,
                'score': user.score,
                'position': current_position
            })
            user_count += 1

        return Response(data=leaderboard)
