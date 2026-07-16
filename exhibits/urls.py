from django.urls import re_path
from django.views.generic import TemplateView

from . import views
from .cache_retry import switch_solr
from django.conf import settings

app_name = 'exhibits'
urlpatterns = [
    re_path(r'^$', views.exhibitRandom, name='randomExplore'),
    re_path(r'jarda-related-resources/$', TemplateView.as_view(template_name='exhibits/jarda-related-resources.html'), name='jarda-related-resources'),
    re_path(r'^search/', views.exhibitSearch, name='exhibitSearch'),
    re_path(r'^browse/(?P<category>[-\w]+)/$', views.exhibitDirectory, name='exhibitDirectory'),
    re_path(r'^(?P<exhibit_id>\d+)/(?P<exhibit_slug>[-\w]+)/$', views.exhibitView, name='exhibitView'),
    re_path(r'^(?P<exhibit_id>\d+)/items/(?P<item_id>.+)/$', views.itemView, name='itemView'),
    re_path(r'^essay/(?P<essay_id>\d+)/(?P<essay_slug>[-\w]+)/$', views.essayView, name='essayView'),
    re_path(r'^t(?P<theme_id>\d+)/(?P<theme_slug>[-_\w]+)/$', views.themeView, name='themeView'),
    re_path(r'^exhibitReport/$', views.exhibitItemView, name='exhibitReport'),
]

if not settings.CALISPHERE:
    registry_urls = [
        re_path(r'^item_health/$', views.item_health, name='itemHealth'),
        re_path(r'^switch-solr/', switch_solr, name='switch_solr')
    ]
    urlpatterns = urlpatterns + registry_urls
