from django.conf.urls import url

from education.views import CourseCreateView, HomeworkTaskCreateView

# TODO: route only POSTs
urlpatterns = [
    url(r'^course$', CourseCreateView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/(?P<lesson_pk>\d+)/homework_task/$', HomeworkTaskCreateView.as_view()),
]
