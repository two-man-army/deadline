import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from decorators import fetch_models
from social.errors import LikeAlreadyExistsError, NonExistentLikeError
from social.models import NewsfeedItem, NewsfeedItemComment
from social.serializers import NewsfeedItemSerializer, NewsfeedItemCommentSerializer
from social.constants import NEWSFEED_ITEMS_PER_PAGE, NW_ITEM_TEXT_POST, NW_ITEM_SHARE_POST
from views import BaseManageView


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
class NewsfeedItemCommentCreateView(CreateAPIView):
    """
        Creates a comment for a NewsfeedItem
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = NewsfeedItemCommentSerializer
    model_classes = (NewsfeedItem, )

    @fetch_models
    def post(self, request, nw_item: NewsfeedItem, *args, **kwargs):
        self.nw_item = nw_item
        self.req_user = request.user
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        return serializer.save(author_id=self.req_user.id, newsfeed_item_id=self.nw_item.id)


# POST /feed/items/{newsfeed_item_id}/comments/{comment_id}
class NewsfeedItemCommentReplyCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = NewsfeedItemCommentSerializer
    model_classes = (NewsfeedItem, NewsfeedItemComment)

    @fetch_models
    def post(self, request, nw_item: NewsfeedItem, nw_item_comment: NewsfeedItemComment, *args, **kwargs):
        if nw_item_comment.newsfeed_item_id != nw_item.id:
            return Response(
                status=400, data={'error': f'Comment {nw_item_comment.id} does not belong to NewsfeedItem {nw_item.id}'}
            )

        self.nw_item = nw_item
        self.user = request.user
        self.comment = nw_item_comment
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        return serializer.save(author_id=self.user.id, newsfeed_item_id=self.nw_item.id, parent=self.comment)
