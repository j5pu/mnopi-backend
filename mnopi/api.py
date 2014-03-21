import datetime
import urlparse
import json

from tastypie import fields
from tastypie.http import HttpCreated
from tastypie.resources import ModelResource
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.validation import Validation
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.utils import trailing_slash, dict_strip_unicode_keys

from django.conf.urls import url
from django.contrib.auth import authenticate
from django.utils.timezone import utc
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from mnopi.models import User, PageVisited, Search, ClientSession, CategorizedDomain, Client
import mnopi.constants
from mnopi import opendns
from mnopi import models_mongo


#TODO: poner un borrado de sessions de vez en cuando?

def get_user_id_from_resource(user_resource):
    return user_resource.rsplit("/", 2)[-2]

class MnopiUserAuthentication(Authentication):
    """
    Basic API authentication which requires username and correct access_key for the user
    """

    def is_authenticated(self, request, **kwargs):

        data = json.loads(request.body)
        user_resource = data.get('user', '')
        session_token = data.get('session_token', '')

        try:
            user = User.objects.get(pk=int(get_user_id_from_resource(user_resource)))
        except Exception:
            return False

        try:
            session = ClientSession.objects.get(session_token=session_token, user=user)
        except ClientSession.DoesNotExist:
            return False

        if session.expiration_time < datetime.datetime.utcnow().replace(tzinfo=utc):
            session.delete()
            return False

        return True

class UserResource(ModelResource):

    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        #fields = ['username'] #TODO: Restrict in production
        allowed_methods = ['get', 'post']
        filtering = {
            "username": ('exact') #TODO : Quitar si es posible
        }

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/login%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('login'), name="api_login"),
            url(r'^(?P<resource_name>%s)/logout%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('logout'), name='api_logout'),
            ]

    @staticmethod
    def generate_user_response(result, reason=None, session_token=None):
        response = {'result': result}
        if reason:
            response['reason'] = reason
        if session_token:
            response['session_token'] = session_token
        return response

    # http://stackoverflow.com/questions/11770501/how-can-i-login-to-django-using-tastypie
    def login(self, request, **kwargs):

        def response_err(reason):
            return self.create_response(request, {
                'result': "ERR",
                'reason': reason
            })

        self.method_check(request, allowed=['post'])

        data = self.deserialize(request, request.body)

        username = data.get('username', '')
        key = data.get('key', '') # password or session token
        renew = data.get('renew', '')
        client = data.get('client', '')


        try:
            client = Client.objects.get(client_name=client)
        except Client.DoesNotExist:
            return response_err("CLIENT_ERROR")

        if not client.allowed:
            return response_err("CLIENT_OUTDATED")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return response_err("INCORRECT_USER_PASSWORD")

        if renew:
            # Use key as session_token for the user, give a new session key
            try:
                session = ClientSession.objects.get(session_token=key, user=user)
            except ClientSession.DoesNotExist:
                return response_err("UNEXPECTED_SESSION")

            if session.expiration_time < datetime.datetime.utcnow().replace(tzinfo=utc):
                session.delete()
                return response_err("UNEXPECTED_SESSION")
            else:
                session.delete()
                session_token = user.new_session(client)

                return self.create_response(request, {
                    'result': "OK",
                    'session_token': session_token,
                    'user_resource': self.get_resource_uri(user)
                })
        else:
            # Manual logging, check user and password and create new session object
            user = authenticate(username=username, password=key)
            if user and user.is_active:
                session_token = user.new_session(client)

                return self.create_response(request, {
                    'result': "OK",
                    'session_token': session_token,
                    'user_resource': self.get_resource_uri(user)
                })
            else:
                return response_err("INCORRECT_USER_PASSWORD")

class PageVisitedValidation(Validation):

    DATE_FORMAT_ACCEPTED = "%Y-%m-%d %H:%M:%S"

    def is_valid(self, bundle, request=None):

        errors = {}
        if 'url' not in bundle.data or bundle.data['url'] == "":
            errors['url'] = "Not specified"
        if 'date' not in bundle.data or bundle.data['date'] == "":
            errors['date'] = "Not specified"
        else:
            try:
                __ = datetime.datetime.strptime(bundle.data['date'], self.DATE_FORMAT_ACCEPTED)
            except:
                errors['date'] = 'Date format must be %Y-%m-%d %H:%M:%S'

        val = URLValidator()
        try:
            val(bundle.data['url'])
        except ValidationError, e:
            errors['url'] = "Must be a valid URL"

        # TODO: Think about Html validation

        return errors


class PageVisitedResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user_resource')

    class Meta:
        queryset = PageVisited.objects.all()
        authentication = MnopiUserAuthentication()
        authorization = Authorization()
        validation = PageVisitedValidation()
        resource_name = 'page_visited'

    def is_valid(self, bundle):
        # Overriden to generate customized overall error
        errors = self._meta.validation.is_valid(bundle, bundle.request)

        if errors:
            bundle.errors = {'result': 'ERR',
                             'reason': 'BAD_PARAMETERS',
                             'erroneous_parameters': errors}
            return False

        return True

    def prepend_urls(self):
        return [url(r"^(?P<resource_name>%s)%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('add_page_visited'), name="add_page"),
                url(r"^(?P<resource_name>%s)/html%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('add_html_visited'), name="add_html")]

    def add_page_visited(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        data = self.deserialize(request, request.body)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(data), request=request)
        self.is_valid(bundle)
        if bundle.errors:
            raise ImmediateHttpResponse(response=self.error_response(bundle.request, bundle.errors))

        url = data.get('url', '')
        user_resource = data.get('user', '')
        date = data.get('date', '')
        html_code = data.get('html_code', '')
        session_token = data.get('session_token', '')

        user = User.objects.get(pk=int(get_user_id_from_resource(user_resource)))
        html_id = ""
        if html_code:
            # Automatic keywords mining is performed when creating the object
            html_id = models_mongo.register_html_visited(page_visited=url, html_code=html_code, user=user.username)

        # TODO: refactor maybe?
        url_domain = urlparse.urlparse(url)[1]
        categories = opendns.getCategories(url_domain)
        categorized_domain = CategorizedDomain.objects.get(domain=url_domain)

        client = ClientSession.objects.get(session_token=session_token).client
        PageVisited.objects.create(user=user, page_visited=url, domain=categorized_domain,
                                   client=client, date=date, html_ref=html_id)
        user.update_categories_visited(categories)

        return self.create_response(request, '', HttpCreated) #TODO: try to send empty data instead of ""

class SearchQueryValidation(Validation):

    DATE_FORMAT_ACCEPTED = "%Y-%m-%d %H:%M:%S"

    def is_valid(self, bundle, request=None):
        errors = {}
        if 'search_query' not in bundle.data or bundle.data['search_query'] == "":
            errors['search_query'] = "Not specified"
        if 'search_results' not in bundle.data or bundle.data['search_results'] == "":
            errors['search_results'] = "Not specified"

        if 'date' not in bundle.data or bundle.data['date'] == "":
            errors['date'] = "Not specified"
        else:
            try:
                __ = datetime.datetime.strptime(bundle.data['date'], self.DATE_FORMAT_ACCEPTED)
            except:
                errors['date'] = 'Date format must be %Y-%m-%d %H:%M:%S'
        # TODO: Specify universal time for server and clients and avoid dates in the future
        # It will be important to check USE_TZ to remain in a consistent client-server-django time state

        val = URLValidator()
        try:
            val(bundle.data['search_results'])
        except ValidationError, e:
            errors['search_results'] = "Search results must be a valid URL"

        return errors


class SearchQueryResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Search.objects.all()
        authentication = MnopiUserAuthentication()
        authorization = Authorization()
        resource_name = 'search_query'
        allowed_methods = ['post']
        validation = SearchQueryValidation()

    def is_valid(self, bundle):
        # Overriden to generate customized overall error
        errors = self._meta.validation.is_valid(bundle, bundle.request)

        if errors:
            bundle.errors = {'result': 'ERR',
                             'reason': 'BAD_PARAMETERS',
                             'erroneous_parameters': errors}
            return False

        return True

    def hydrate(self, bundle):
        #bundle.obj.user = UserResource().get_via_uri(bundle.data['user_resource'])

        # Get the client from the current session
        bundle.obj.client = ClientSession.objects.get(session_token=bundle.data['session_token']).client

        return bundle