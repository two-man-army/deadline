from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, CharField

from private_chat.models import Message


class MessageSerializer(ModelSerializer):
    sender_name = CharField(source='sender.username')
    message = CharField(source='text')
    created = SerializerMethodField()

    class Meta:
        fields = ('id', 'sender_name', 'message', 'created')
        model = Message

    def get_created(self, instance: Message):
        return instance.get_formatted_create_datetime()
