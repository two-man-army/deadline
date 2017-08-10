from django.conf.urls import url

from challenges.views import (
    ChallengeDetailView, SubmissionDetailView, TestCaseDetailView, TestCaseListView,
    SubmissionCreateView, SubmissionListView, TopSubmissionListView, MainCategoryListView, SubCategoryDetailView,
    LatestAttemptedChallengesListView, LanguageDetailView, SelfTopSubmissionDetailView,
    CastSubmissionVoteView, RemoveSubmissionVoteView, SelfGetLeaderboardPositionView,
    GetLeaderboardView, LanguageListView, SubmissionCommentManageView, ChallengeCommentManageView)
from django.views.decorators.cache import cache_page, never_cache

urlpatterns = [
    url(r'^latest_attempted$', cache_page(60)(LatestAttemptedChallengesListView.as_view()), name='latest_challenges'),

    url(r'^categories/all$', cache_page(60*60)(MainCategoryListView.as_view()), name='category_list'),
    url(r'^subcategories/(?P<name>[^/]+)$', cache_page(60*60)(SubCategoryDetailView.as_view()), name='subcategory_detail'),
    url(r'^languages/(?P<name>[^/]+)$', cache_page(60*60)(LanguageDetailView.as_view()), name='language_detail'),
    url(r'^languages$', LanguageListView.as_view(), name='language_list'),

    url(r'^(?P<pk>\d+)$', cache_page(5)(ChallengeDetailView.as_view()), name='challenge_detail'),
    url(r'^(?P<challenge_pk>\d+)/comments$', ChallengeCommentManageView.as_view(), name='challenge_comment'),

    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<pk>\d+)$', SubmissionDetailView.as_view(), name='submission_detail'),
    url(r'^(?P<challenge_pk>\d+)/submissions/new$', SubmissionCreateView.as_view(), name='submission_create'),
    url(r'^(?P<challenge_pk>\d+)/submissions/all$', cache_page(20)(SubmissionListView.as_view()), name='submission_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/top$', TopSubmissionListView.as_view(), name='top_submission_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_id>\d+)/comments', SubmissionCommentManageView.as_view(), name='submission_comment'),
    url(r'^submissions/(?P<submission_id>\d+)/vote$', CastSubmissionVoteView.as_view(), name='vote_submission'),
    url(r'^submissions/(?P<submission_id>\d+)/removeVote$', RemoveSubmissionVoteView.as_view(), name='remove_submission_vote'),
    url(r'^(?P<challenge_pk>\d+)/submissions/selfTop$', SelfTopSubmissionDetailView.as_view(), name='self_top_submission'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/tests$', cache_page(60)(TestCaseListView.as_view()),
        name='test_case_list'),
    url(r'^(?P<challenge_pk>\d+)/submissions/(?P<submission_pk>\d+)/test/(?P<pk>\d+)$', cache_page(60*60)(TestCaseDetailView.as_view()),
        name='test_case_detail'),

    url(r'^selfLeaderboardPosition$', SelfGetLeaderboardPositionView.as_view(),
        name='self_leaderboard_position'),

    url(r'^getLeaderboard$', cache_page(30)(GetLeaderboardView.as_view()), name='leaderboard'),
]
