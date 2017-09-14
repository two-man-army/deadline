from collections import OrderedDict

from django.db import models
from rest_framework import serializers
from rest_framework_hstore.fields import HStoreField

from serializers import RecursiveField
from accounts.serializers import UserSerializer
from social.constants import NW_ITEM_SHARE_POST
from social.models import NewsfeedItemComment, NewsfeedItem, NewsfeedItemLike, Notification


class NotificationSerializer(serializers.ModelSerializer):
    content = serializers.JSONField()

    class Meta:
        model = Notification
        fields = ('id', 'type', 'updated_at', 'content')


class NewsfeedItemCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = RecursiveField(many=True, read_only=True)
    content = serializers.CharField(max_length=500, min_length=2, allow_blank=False)

    class Meta:
        model = NewsfeedItemComment
        fields = ('id', 'content', 'author', 'replies')
        read_only_fields = ('id', 'author', 'replies')


class NewsfeedItemListSerializer(serializers.ListSerializer):
    """
    Override the ListSerializer class to pass the optional user variable
        to the 'to_representation()' call of each NewsfeedItemSerializer
    """
    def to_representation(self, data, user=None):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        # Dealing with nested relationships, data can be a Manager,
        # so, first get a queryset from the Manager if needed
        iterable = data.all() if isinstance(data, models.Manager) else data

        return [
            self.child.to_representation(item, user) for item in iterable
        ]


class NewsfeedItemSerializer(serializers.ModelSerializer):
    like_count = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    comments = NewsfeedItemCommentSerializer(many=True, read_only=True)
    content = HStoreField()

    class Meta:
        model = NewsfeedItem
        fields = '__all__'
        list_serializer_class = NewsfeedItemListSerializer

    def get_like_count(self, obj):
        return obj.likes.count()

    def to_representation(self, instance, user=None):
        result: OrderedDict = super().to_representation(instance)

        if instance.type == NW_ITEM_SHARE_POST:
            self._handle_share_serialization(data=result, instance=instance)

        # add a user_has_liked field
        if user is not None:
            result['user_has_liked'] = NewsfeedItemLike.objects.filter(author=user, newsfeed_item=instance).exists()

        return result

    def _handle_share_serialization(self, data: OrderedDict, instance: NewsfeedItem):
        """
        If this NewsfeedItem is a share, serialize the Item it shares and attach it to our data
        """
        shared_item_id = instance.content['newsfeed_item_id']
        data['shared_item'] = OrderedDict()

        try:
            shared_item = NewsfeedItem.objects.get(id=shared_item_id)
            shared_item_data = self.__class__(instance=shared_item).data
            for field_key, field_value in shared_item_data.items():
                data['shared_item'][field_key] = field_value
        except NewsfeedItem.DoesNotExist:
            raise Exception(f'Newsfeed Item {instance.id} has shared a NewsfeedItem (ID: '
                            f'{shared_item_id}) that does not exist!')
