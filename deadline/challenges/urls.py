from django.conf.urls import url

from challenges.views import ChallengeDetailView

urlpatterns = [
    url(r'^(?P<pk>\d+)', ChallengeDetailView.as_view(), name='challenge'),
]
