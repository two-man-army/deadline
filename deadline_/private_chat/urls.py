from django.conf.urls import url, include

from private_chat.views import PreviousMessagesListView

urlpatterns = [
    url(r'^messages$', PreviousMessagesListView.as_view())
]
