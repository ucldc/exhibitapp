from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.lessonPlanDirectory, name='lessonPlanDirectory'),
    re_path(r'^(?P<lesson_id>\d+)/(?P<lesson_slug>[-\w]+)/$', views.lessonPlanView, name='lessonPlanView'),
    re_path(r'^(?P<lesson_id>\d+)/items/(?P<item_id>.+)/$', views.lessonPlanItemView, name='lessonPlanItemView'),
]