from django.conf.urls import url

from challenges.views import (
    ChallengeDetailView, SubmissionDetailView, TestCaseDetailView, TestCaseListView,
    SubmissionCreateView, SubmissionListView, TopSubmissionListView,ChallengeCategoryListView, SubCategoryDetailView)

urlpatterns = [
    url(r'^categories/all$', ChallengeCategoryListView.as_view(), name='category_list'),
    url(r'^subcategories/(?P<pk>[^/]+)$', SubCategoryDetailView.as_view(), name='subcategory_detail'),
    url(r'^(?P<pk>\d+)$', ChallengeDetailView.as_view(), name='challenge_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<pk>\d+)$', SubmissionDetailView.as_view(), name='submission_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/new$', SubmissionCreateView.as_view(), name='submission_create'),
    url(r'^(?P<challenge_pk>\d+)/submissions/all$', SubmissionListView.as_view(), name='submission_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/top$', TopSubmissionListView.as_view(), name='top_submission_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/test/(?P<pk>\d+)$', TestCaseDetailView.as_view(),
        name='test_case_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/tests$', TestCaseListView.as_view(),
        name='test_case_list'),
]
