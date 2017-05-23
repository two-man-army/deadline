from django.conf.urls import url

from challenges.views import (
    ChallengeDetailView, SubmissionDetailView, TestCaseDetailView, TestCaseListView,
    SubmissionCreateView, SubmissionListView, TopSubmissionListView, MainCategoryListView, SubCategoryDetailView,
    LatestAttemptedChallengesListView, LanguageDetailView, SelfTopSubmissionDetailView)

urlpatterns = [
    url(r'^latest_attempted$', LatestAttemptedChallengesListView.as_view(), name='latest_challenges'),

    url(r'^categories/all$', MainCategoryListView.as_view(), name='category_list'),
    url(r'^subcategories/(?P<pk>[^/]+)$', SubCategoryDetailView.as_view(), name='subcategory_detail'),
    url(r'^languages/(?P<name>[^/]+)$', LanguageDetailView.as_view(), name='language_detail'),
    url(r'^(?P<pk>\d+)$', ChallengeDetailView.as_view(), name='challenge_detail'),

    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<pk>\d+)$', SubmissionDetailView.as_view(), name='submission_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/new$', SubmissionCreateView.as_view(), name='submission_create'),
    url(r'^(?P<challenge_pk>\d+)/submissions/all$', SubmissionListView.as_view(), name='submission_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/top$', TopSubmissionListView.as_view(), name='top_submission_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/selfTop$', SelfTopSubmissionDetailView.as_view(), name='self_top_submission'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/tests$', TestCaseListView.as_view(),
        name='test_case_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/test/(?P<pk>\d+)$', TestCaseDetailView.as_view(),
        name='test_case_detail'),
]
