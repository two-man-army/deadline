from rest_framework import serializers

from accounts.serializers import UserSerializer
from errors import DisabledSerializerError
from social.models import NewsfeedItemComment


class NewsfeedItemCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = NewsfeedItemComment
        fields = ('id', 'content', 'author')
        read_only_fields = ('id', 'content', 'author')

    def save(self, **kwargs):
        raise DisabledSerializerError('Saving this serializer is disabled!')
