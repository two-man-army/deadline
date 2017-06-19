from django.conf.urls import url

from education.views import CourseCreateView

urlpatterns = [
    url(r'^course$', CourseCreateView.as_view())
]
