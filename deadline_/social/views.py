import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone

from accounts.models import User
from challenges.models import Submission, Challenge
from decorators import fetch_models
from helpers import get_date_difference
from social.errors import LikeAlreadyExistsError, NonExistentLikeError
from social.models import NewsfeedItem, NewsfeedItemComment, Notification
from social.serializers import NewsfeedItemSerializer, NewsfeedItemCommentSerializer, NotificationSerializer
from social.constants import NEWSFEED_ITEMS_PER_PAGE, NW_ITEM_TEXT_POST, NW_ITEM_SHARE_POST, \
    NW_ITEM_SUBMISSION_LINK_POST, NW_ITEM_CHALLENGE_LINK_POST, NW_ITEM_CHALLENGE_COMPLETION_POST, \
    MAX_CHALLENGE_COMPLETION_SUBMISSION_EXPIRY_MINUTES
from views import BaseManageView

"""
Huge TODO: (Pre-Release)
    We will need some kind of anti-spam for Comments and Post creation,
        otherwise our site will quickly get overrun by bots,
        malicious users or just spammer kids
"""


def follow_decorator(view_func, *args, **kwargs):
    def _follow(request, *args, **kwargs):
        if 'target' not in request.GET:
            return Response(status=400, data={'error': f'Follow target missing'})
        if not re.fullmatch(r'^\d+$', request.GET['target']):
            return Response(status=400, data={'error': f'Target querystring must be an integer!'})

        target_user_id = request.GET['target']
        try:
            user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response(status=404)

        return view_func(request, user, *args, **kwargs)
    return _follow


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@follow_decorator
def follow(request: Request, user: User):
    if user in request.user.users_followed.all():
        return Response(status=400, data={'error': f'You have already followed user {user.username}'})

    request.user.follow(user)
    return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@follow_decorator
def unfollow(request: Request, user: User):
    if user not in request.user.users_followed.all():
        return Response(status=400, data={'error': f'You have not followed user {user.username}'})

    request.user.unfollow(user)
    return Response(status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_token(request: Request):
    if request.user.notification_token_is_expired():
        request.user.refresh_notification_token()

    return Response(status=200, data={'token': request.user.notification_token})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unseen_notifications(request: Request, *args, **kwargs):
    """
    Returns all the unseen notifications for a user
    """
    return Response(status=200, data=NotificationSerializer(
        instance=Notification.fetch_unread_notifications_for_user(request.user),
        many=True).data)


class NotificationReadView(APIView):
    """
    Given a list of notification IDs, marks all of them as read
    """
    permission_classes = (IsAuthenticated, )

    def put(self, request, *args, **kwargs):
        if 'notifications' not in request.data or not all(type(item) == int for item in request.data['notifications']):
            return Response(status=400,
                            data={'error': f'Invalid request data, notifications must a list of notification IDs'})

        Notification.objects.filter(id__in=request.data['notifications'], recipient=request.user).update(is_read=True)
        return Response(status=200)


class NotificationManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': lambda *args: unseen_notifications,
        'PUT': NotificationReadView.as_view
    }


class TextPostCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = NewsfeedItemSerializer

    def create(self, request, *args, **kwargs):
        """
        We are always creating a TextPost NewsfeedItem,
            and as such we always set the type, content dictionary structure
        We also prevent the user to modify the created_at, updated_at and author variables
        """
        self.author_id = request.user.id

        request.data['type'] = NW_ITEM_TEXT_POST
        request.data['content'] = {
            'content': request.data['content']
        }
        request.data.pop('created_at', None)
        request.data.pop('updated_at', None)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author_id=self.author_id)


class SubmissionLinkPostCreateView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        submission_id = request.data.get('submission_id', None)
        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response(status=404, data={'error': f'Submission with ID {submission_id} does not exist!'})

        # validate that the current User is either the author or has solved it perfectly, otherwise he cannot share it
        if submission.author_id != request.user.id and not submission.challenge.is_solved_by_user(request.user):
            # User has not fully solved this and as such does not have access to the solution
            return Response(data={'error': 'You have not fully solved the challenge'}, status=400)

        NewsfeedItem.objects.create_submission_link(submission=submission, author=request.user)
        return Response(status=201)


class ChallengeLinkPostCreateView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        challenge_id = request.data.get('challenge_id', None)
        try:
            challenge = Challenge.objects.get(id=challenge_id)
        except Challenge.DoesNotExist:
            return Response(status=404, data={'error': f'Challenge with ID {challenge_id} does not exist!'})

        NewsfeedItem.objects.create_challenge_link(challenge=challenge, author=request.user)
        return Response(status=201)


# TODO: Maybe create some decorator which validates that the requires fields in request.data are sent
class ChallengeCompletionPostCreateView(APIView):
    """
    Creates a NewsfeedItem of type CHALLENGE_COMPLETION_POST
    Used for when a User completes a challenge and wants to share that fact
    ex: Stanislav just completed Basic Numbers with score 100/100 after 40 attempts!
    """
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        submission_id = request.data.get('submission_id', None)
        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response(status=404, data={'error': f'Submission with ID {submission_id} does not exist!'})

        # validate that the submission's author is the request user
        if submission.author_id != request.user.id:
            return Response(status=400, data={'error': f'Submission {submission.id} does not belong to '
                                                       f'User with ID {request.user.id}'})
        # validate that this submission has solved the challenge
        if not submission.has_solved_challenge():
            return Response(status=400, data={'error': f'Submission {submission.id} has not fully solved the challenge!'
                                                       f' ({submission.result_score}/{submission.challenge.score}) Score'})
        # validate that the submission is made in the allowed timeframe
        minutes_since_submission = get_date_difference(
            end_date=timezone.now(),
            start_date=submission.created_at).total_seconds() // 60
        if minutes_since_submission > MAX_CHALLENGE_COMPLETION_SUBMISSION_EXPIRY_MINUTES:
            return Response(status=400, data={'error': f'Submission {submission.id} is not '
                                                       f'eligible for a CHALLENGE_COMPLETION post!'})
        NewsfeedItem.objects.create_challenge_completion_post(submission=submission)
        return Response(status=201)


# POST /posts
class PostCreateView(APIView):
    """
    This handles NewsfeedItem Post creations, delegating it to the specific View according to the
        type of post being created
    """
    VIEWS_BY_TYPE = {
        NW_ITEM_TEXT_POST: TextPostCreateView.as_view,
        NW_ITEM_SUBMISSION_LINK_POST: SubmissionLinkPostCreateView.as_view,
        NW_ITEM_CHALLENGE_LINK_POST: ChallengeLinkPostCreateView.as_view,
        NW_ITEM_CHALLENGE_COMPLETION_POST: ChallengeCompletionPostCreateView.as_view,
    }

    def dispatch(self, request, *args, **kwargs):
        post_type = request.POST.get('post_type', None)
        if post_type not in self.VIEWS_BY_TYPE:
            return super().dispatch(request, *args, **kwargs)

        return self.VIEWS_BY_TYPE[post_type]()(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return Response(status=400, data={'error': 'Post Type is not supported!'})


class NewsfeedContentView(APIView):
    """
    This view returns all the content (NewsfeedItems) that a user should see
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        try:
            page = int(request.GET.get('page', 1)) - 1
        except ValueError:
            page = 0

        serializer = NewsfeedItemSerializer(many=True)

        start_offset = page * NEWSFEED_ITEMS_PER_PAGE
        # TODO: For NewsfeedItems which are SubmissionLinks, validate that the current user can see them otherwise dont show them :)
        nw_items: [NewsfeedItem] = request.user.fetch_newsfeed(start_offset=start_offset, end_limit=start_offset + NEWSFEED_ITEMS_PER_PAGE)
        
        return Response(
            data={
                'items': serializer.to_representation(nw_items, user=request.user)
            }
        )


# GET /feed/items/{newsfeed_item_id}
class NewsfeedItemDetailView(RetrieveAPIView):
    """
        Returns information about a specific NewsfeedItem
    """
    permission_classes = (IsAuthenticated, )
    queryset = NewsfeedItem.objects.all()
    serializer_class = NewsfeedItemSerializer


# POST /feed/items/{newsfeed_item_id}
class SharePostCreateView(APIView):
    """
        Creates a NewsfeedItem of type SHARE_POST
    """
    permission_classes = (IsAuthenticated, )
    model_classes = (NewsfeedItem, )

    @fetch_models
    def post(self, request, nw_item: NewsfeedItem, *args, **kwargs):
        if nw_item.type == NW_ITEM_SHARE_POST:
            return Response(status=400, data={'error': 'You cannot share a share NewsfeedItem!'})
        NewsfeedItem.objects.create_share_post(author=request.user, shared_item=nw_item)
        return Response(status=201)


# /feed/items/{newsfeed_item_id}
class NewsfeedItemDetailManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'GET': NewsfeedItemDetailView.as_view,
        'POST': SharePostCreateView.as_view
    }


# POST /feed/items/{newsfeed_item_id}/likes
class NewsfeedItemLikeCreateView(APIView):
    """
    Adds a like to a NewsfeedItem
    """
    permission_classes = (IsAuthenticated, )
    model_classes = (NewsfeedItem, )

    @fetch_models
    def post(self, request, nw_item: NewsfeedItem, *args, **kwargs):
        try:
            nw_item.like(request.user)
        except LikeAlreadyExistsError:
            return Response(status=400, data={'error': 'You have already liked that post!'})

        return Response(status=201)


# DELETE /feed/items/{newsfeed_item_id}/likes
class NewsfeedItemLikeDeleteView(APIView):
    """ Removes a like from a NewsfeedItem """
    permission_classes = (IsAuthenticated, )
    model_classes = (NewsfeedItem, )

    @fetch_models
    def delete(self, request, nw_item: NewsfeedItem, *args, **kwargs):
        try:
            nw_item.remove_like(request.user)
        except NonExistentLikeError:
            return Response(status=400, data={'error': 'You have have not liked that post!'})

        return Response(status=200)


# /feed/items/{newsfeed_item_id}/likes
class NewsfeedItemLikeManageView(BaseManageView):
    VIEWS_BY_METHOD = {
        'POST': NewsfeedItemLikeCreateView.as_view,
        'DELETE': NewsfeedItemLikeDeleteView.as_view
    }


# POST /feed/items/{newsfeed_item_id}/comments
class NewsfeedItemCommentCreateView(APIView):
    """
        Creates a comment for a NewsfeedItem
    """
    permission_classes = (IsAuthenticated, )
    model_classes = (NewsfeedItem, )

    @fetch_models
    def post(self, request, nw_item: NewsfeedItem, *args, **kwargs):
        ser = NewsfeedItemCommentSerializer(data=request.data)
        if not ser.is_valid():
            return Response(status=400, data={'error': ser.errors})

        nw_item.add_comment(author=request.user, content=request.data['content'])

        return Response(status=201)


# POST /feed/items/{newsfeed_item_id}/comments/{comment_id}
class NewsfeedItemCommentReplyCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, )
    model_classes = (NewsfeedItem, NewsfeedItemComment)

    @fetch_models
    def post(self, request, nw_item: NewsfeedItem, nw_item_comment: NewsfeedItemComment, *args, **kwargs):
        if nw_item_comment.newsfeed_item_id != nw_item.id:
            return Response(
                status=400, data={'error': f'Comment {nw_item_comment.id} does not belong to NewsfeedItem {nw_item.id}'}
            )

        ser = NewsfeedItemCommentSerializer(data=request.data)
        if not ser.is_valid():
            return Response(status=400, data={'error': ser.errors})

        nw_item_comment.add_reply(author=request.user, content=request.data['content'], to_notify=True)

        return Response(status=201)
