from django.conf.urls import url

from challenges.views import ChallengeDetailView, SubmissionDetailView

urlpatterns = [
    url(r'^(?P<pk>\d+)$', ChallengeDetailView.as_view(), name='challenge_detail'),
    url(r'^\d+/submissions/(?P<pk>\d+)$', SubmissionDetailView.as_view(), name='submission_detail')
]
