from django.conf.urls.defaults import *
from views import UserPagesVisitedList, UserSearchesDoneList, UserSiteKeywordsList, UserMetaKeywordsList

urlpatterns = patterns(
    'mnopi.views',

    url(r'^$', 'index', name='index'),
    url(r'^login', 'login_user', name='login'),
    url(r'^plugin_login', 'plugin_login', name='plugin_login'),
    url(r'^logout', 'logout_user', name='logout'),
    url(r'^register', 'register', name='register'),
    url(r'^conditions', 'conditions', name='conditions'),
    url(r'^plugin', 'plugin', name='plugin'),
    url(r'^dashboard/$', 'dashboard', name='dashboard'),
    url(r'^dashboard/pages/$', UserPagesVisitedList.as_view(), name='user_visited_pages'),
    url(r'^dashboard/pages/(?P<limit>\d+)/', UserPagesVisitedList.as_view(), name='user_visited_pages'),
    url(r'^dashboard/searches/$', UserSearchesDoneList.as_view(), name='user_searches_done'),
    url(r'^dashboard/searches/(?P<limit>\d+)/', UserPagesVisitedList.as_view(), name='user_visited_pages'),
    url(r'^dashboard/search/', 'search_user_data', name='search_user_data'),

    url(r'^dashboard/site_keywords', UserSiteKeywordsList.as_view(), name='user_site_keywords'),
    url(r'^dashboard/meta_keywords', UserMetaKeywordsList.as_view(), name='user_meta_keywords'),
    url(r'^dashboard/search_results', 'search_results', name='search_results'),
    url(r'^profiler', 'profiler', name='profiler'),

    # POST services
    url(r'^new_user', 'new_user', name='new_user'),
    url(r'^sendPageVisited', 'page_visited', name='page_visited'),
    url(r'^sendSearch', 'search_done', name='search_done'),
    url(r'^sendHtmlVisited', 'html_visited', name='html_visited'),

    # Deprecated, use it only for testing purposes
    # TODO: DELETE on production
    url(r'^keywords/(\w+)/$', 'user_keywords', name='user_keywords'),

)
