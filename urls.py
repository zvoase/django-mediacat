from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^cat/$', 'mediacat.views.cat'),
)