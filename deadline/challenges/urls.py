from django.conf.urls import url

from challenges.views import ChallengeDetailView, SubmissionDetailView, TestCaseDetailView, TestCaseListView, SubmissionCreateView

urlpatterns = [
    url(r'^(?P<pk>\d+)$', ChallengeDetailView.as_view(), name='challenge_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<pk>\d+)$', SubmissionDetailView.as_view(), name='submission_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/new$', SubmissionCreateView.as_view(), name='submission_create'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/test/(?P<pk>\d+)$', TestCaseDetailView.as_view(),
        name='test_case_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/tests$', TestCaseListView.as_view(),
        name='test_case_list'),
]
