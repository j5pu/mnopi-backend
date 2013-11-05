from django.conf.urls.defaults import *


urlpatterns = patterns(
    'mnopi.views',

    url(r'^$', 'index', name='index'),
    url(r'^login', 'login', name='login'),
    url(r'^register', 'register', name='register'),
    url(r'^conditions', 'conditions', name='conditions'),

    # Post services
    url(r'^new_user', 'new_user', name='new_user'),
    url(r'^sendPageVisited', 'page_visited', name='page_visited'),
    url(r'^sendSearch', 'search_done', name='search_done'),
    url(r'^sendHtmlVisited', 'html_visited', name='html_visited'),

)
