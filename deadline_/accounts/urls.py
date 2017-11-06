from django.conf.urls import url

from accounts import views


urlpatterns = [
    url(r'^register/', views.register, name='register'),
    url(r'^login/', views.login, name='login'),
    url(r'^user/(?P<pk>\d+)/$', views.UserDetailView.as_view(), name='user_detail'),
    url(r'^user/(?P<pk>\d+)/profile$', views.ProfilePageView.as_view(), name='user_profile_page'),
    url(r'^user/(?P<pk>\d+)/recent_submissions$', views.UserRecentSubmissionCount.as_view(),
        name='user_recent_submissions_count'),
    url(r'^get_csrf/', views.index, name='get_csrf')
]
