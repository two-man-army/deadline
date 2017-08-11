import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from decorators import fetch_models
from social.models import NewsfeedItem
from social.serializers import NewsfeedItemSerializer
from social.constants import NEWSFEED_ITEMS_PER_PAGE


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

        request.data['type'] = 'TEXT_POST'
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
