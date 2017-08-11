from django.conf.urls import url

from social import views


urlpatterns = [
    url(r'^follow$', views.follow, name='user_follow'),
    url(r'^unfollow$', views.unfollow, name='user_unfollow'),
    url(r'^posts$', views.TextPostCreateView.as_view(), name='create_text_post'),
    url(r'^feed$', views.NewsfeedContentView.as_view(), name='newsfeed'),
    url(r'^feed/items/(?P<pk>\d+)$', views.NewsfeedItemDetailView.as_view(), name='newsfeed_item_detail'),
    url(r'^feed/items/(?P<pk>\d+)/comments$', views.NewsfeedItemCommentCreateView.as_view(), name='newsfeed_item_detail'),
]
