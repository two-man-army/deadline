from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from private_chat.constants import PMS_PER_QUERY
from private_chat.models import Message, Dialog
from private_chat.serializers import MessageSerializer


class PreviousMessagesListView(APIView):
    """
    This view is called to fetch PMS_PER_QUERY messages between two users, all sent before a given message
    Requires
        - querystring before_pm - the id of the message we want the results to be before
        - conversation_token - the token with which you authenticate yourself.
            Unique for every conversation and is refreshed frequently
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        before_pm, is_err, err_msg = self.validate_and_fetch(request.GET.get('conversation_token'),
                                                             request.GET.get('before_pm'))
        if is_err:
            return Response(status=400, data={'error': err_msg})

        messages: [Message] = Message.fetch_messages_from_dialog_created_before(message=before_pm,
                                                                                message_count=PMS_PER_QUERY)

        return Response(status=200, data={'messages': MessageSerializer(instance=messages, many=True).data})

    def validate_and_fetch(self, conversation_token, before_pm_id) -> (Message, bool, str):
        try:
            before_pm: Message = Message.objects.get(id=before_pm_id)
        except Message.DoesNotExist:
            return None, True, f'Message with ID {before_pm_id} does not exist!'
        dialog: Dialog = before_pm.dialog
        if dialog.owner != self.request.user and dialog.opponent != self.request.user:
            return None, True, f'You do not participate in that dialog!'

        if not dialog.token_is_valid(conversation_token):
            return None, True, f'Token #{conversation_token} is not valid!'

        return before_pm, False, ''
