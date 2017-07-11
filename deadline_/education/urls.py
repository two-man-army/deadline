from django.conf.urls import url

from education.views import CourseCreateView, HomeworkTaskCreateView, HomeworkTaskTestCreateView, LessonManageView, \
    LessonCreateView, CourseManageView, TaskSubmissionCreateView, CourseLanguageDeleteView, CourseLanguageAddView

# TODO: route only POSTs
urlpatterns = [
    url(r'^course$', CourseCreateView.as_view()),
    url(r'^course/(?P<pk>\d+)$', CourseManageView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/$', LessonCreateView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/(?P<pk>\d+)$', LessonManageView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/language/(?P<pk>\d+)$', CourseLanguageDeleteView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/language/$', CourseLanguageAddView.as_view()),
    # TODO: Create Homework UR
    # TODO: Lock Course/lesson/hoemwork URL
    url(r'^course/(?P<course_pk>\d+)/lesson/(?P<lesson_pk>\d+)/homework_task/$', HomeworkTaskCreateView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/(?P<lesson_pk>\d+)/homework_task/(?P<task_pk>\d+)/submission', TaskSubmissionCreateView.as_view()),
    url(r'^course/(?P<course_pk>\d+)/lesson/(?P<lesson_pk>\d+)/homework_task/(?P<task_pk>\d+)/test',
        HomeworkTaskTestCreateView.as_view()),
]
