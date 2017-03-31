from django.conf.urls import url

from accounts import views


urlpatterns = [
    url(r'^register/', views.register, name='register'),
    url(r'^login/', views.login, name='login'),
    url(r'^user/(?P<pk>.+)', views.UserDetailView.as_view(), name='user_detail'),
    url(r'^get_csrf/', views.index, name='get_csrf')
]
