from django.conf.urls import patterns, include, url
from tastypie.api import Api

from mnopi.api import PageVisitedResource, SearchQueryResource, UserResource

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(PageVisitedResource())
v1_api.register(SearchQueryResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mnopiBackend.views.home', name='home'),
    # url(r'^mnopiBackend/', include('mnopiBackend.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^api/', include(v1_api.urls), name="api"),
    url(r'^', include('mnopi.urls'))

)

