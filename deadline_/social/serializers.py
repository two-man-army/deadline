from rest_framework import serializers
from rest_framework_hstore.fields import HStoreField

from accounts.serializers import UserSerializer
from errors import DisabledSerializerError
from social.models import NewsfeedItemComment, NewsfeedItem


class NewsfeedItemCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = NewsfeedItemComment
        fields = ('id', 'content', 'author')
        read_only_fields = ('id', 'content', 'author')

    def save(self, **kwargs):
        raise DisabledSerializerError('Saving this serializer is disabled!')


class NewsfeedItemSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = NewsfeedItemCommentSerializer(many=True, read_only=True)
    content = HStoreField()

    class Meta:
        model = NewsfeedItem
        fields = '__all__'
