from django.conf.urls import url

from accounts import views


urlpatterns = [
    url(r'^register/', views.register, name='register'),
    url(r'^login/', views.login, name='login'),
    url(r'^user/(?P<pk>.+)', views.UserDetailView.as_view(), name='user_detail'),
    url(r'^follow$', views.follow, name='user_follow'),
    url(r'^unfollow', views.unfollow, name='user_unfollow'),
    url(r'^get_csrf/', views.index, name='get_csrf')
]
