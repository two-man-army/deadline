from django.conf.urls import url

from social import views


urlpatterns = [
    url(r'^follow$', views.follow, name='user_follow'),
    url(r'^unfollow', views.unfollow, name='user_unfollow'),
]
