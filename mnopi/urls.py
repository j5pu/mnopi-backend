from django.conf.urls.defaults import *
from views import UserPagesVisitedList, UserSearchesDoneList

urlpatterns = patterns(
    'mnopi.views',

    url(r'^$', 'index', name='index'),
    url(r'^login', 'login_user', name='login'),
    url(r'^logout', 'logout_user', name='logout'),
    url(r'^register', 'register', name='register'),
    url(r'^conditions', 'conditions', name='conditions'),
    url(r'^plugin', 'plugin', name='plugin'),
    url(r'^dashboard/$', 'dashboard', name='dashboard'),
    url(r'^dashboard/pages', UserPagesVisitedList.as_view(), name='user_visited_pages'),
    url(r'^dashboard/searches', UserSearchesDoneList.as_view(), name='user_searches_done'),
    url(r'^test', 'test'),

    # POST services
    url(r'^new_user', 'new_user', name='new_user'),
    url(r'^sendPageVisited', 'page_visited', name='page_visited'),
    url(r'^sendSearch', 'search_done', name='search_done'),
    url(r'^sendHtmlVisited', 'html_visited', name='html_visited'),

    # GET services
    url(r'^keywords/(\w+)/$', 'user_keywords', name='user_keywords'),

)
