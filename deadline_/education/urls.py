from django.conf.urls import url

from education.views import CourseCreateView, HomeworkTaskCreateView, HomeworkTaskTestCreateView, LessonCreateView

# TODO: route only POSTs
urlpatterns = [
    url(r'^course$', CourseCreateView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/$', LessonCreateView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/(?P<lesson_pk>\d+)/homework_task/$', HomeworkTaskCreateView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/(?P<lesson_pk>\d+)/homework_task/(?P<task_pk>\d+)/test',
        HomeworkTaskTestCreateView.as_view()),
]
