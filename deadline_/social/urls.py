from django.conf.urls import url

from social import views


urlpatterns = [
    url(r'^follow$', views.follow, name='user_follow'),
    url(r'^unfollow$', views.unfollow, name='user_unfollow'),
    url(r'^posts$', views.PostCreateView.as_view(), name='create_post'),
    url(r'^feed$', views.NewsfeedContentView.as_view(), name='newsfeed'),
    url(r'^feed/items/(?P<pk>\d+)$', views.NewsfeedItemDetailManageView.as_view(), name='newsfeed_item_detail'),
    url(r'^feed/items/(?P<pk>\d+)/likes$$', views.NewsfeedItemLikeManageView.as_view(), name='newsfeed_likes_views'),
    url(r'^feed/items/(?P<pk>\d+)/comments$', views.NewsfeedItemCommentCreateView.as_view(), name='newsfeed_comment_create'),
    url(r'^feed/items/(?P<nw_item_pk>\d+)/comments/(?P<pk>\d+)$', views.NewsfeedItemCommentReplyCreateView.as_view(),
        name='newsfeed_comment_reply_create'),

    url(r'^notifications/token$', views.notification_token, name='notification_token'),
]
