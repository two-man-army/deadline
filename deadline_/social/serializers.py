from collections import OrderedDict

from django.db import models
from rest_framework import serializers
from rest_framework_hstore.fields import HStoreField

from serializers import RecursiveField
from accounts.serializers import UserSerializer
from errors import DisabledSerializerError
from social.models import NewsfeedItemComment, NewsfeedItem, NewsfeedItemLike


class NewsfeedItemCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = RecursiveField(many=True, read_only=True)

    class Meta:
        model = NewsfeedItemComment
        fields = ('id', 'content', 'author', 'replies')
        read_only_fields = ('id', 'content', 'author', 'replies')

    def save(self, **kwargs):
        raise DisabledSerializerError('Saving this serializer is disabled!')


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

        # add a user_has_liked field to those who want it
        if user is not None:
            result['user_has_liked'] = NewsfeedItemLike.objects.filter(author=user, newsfeed_item=instance).exists()

        return result
