from django.conf.urls import patterns, include, url

from settings import MEDIA_ROOT

urlpatterns = patterns('',
    url(r'^$', 'machine_learning.views.index'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    url(r'^create/$', 'machine_learning.views.create'),
    url(r'^delete/(?P<problem_id>\d+)/$', 'machine_learning.views.delete'),
    url(r'^download/(?P<problem_id>\d+)/$', 'machine_learning.views.download'),
    url(r'^edit/(?P<problem_id>\d+)/$', 'machine_learning.views.edit'),
    url(r'^timer/(?P<problem_id>\d+)/$', 'machine_learning.views.timer'),
    url(r'^user/(?P<user_id>\d+)/$', 'machine_learning.views.user'),
    url(r'^view/(?P<problem_id>\d+)/$', 'machine_learning.views.view'),

    url(r'^ranking/$', 'machine_learning.views.ranking'),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT}),
)
