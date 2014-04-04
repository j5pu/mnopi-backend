import datetime
import urlparse
import json

from tastypie import fields, http
from tastypie.http import HttpCreated
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.validation import Validation
from tastypie.exceptions import ImmediateHttpResponse, Unauthorized
from tastypie.utils import trailing_slash, dict_strip_unicode_keys

from django.conf.urls import url
from django.contrib.auth import authenticate
from django.utils.timezone import utc
from django.core.validators import URLValidator, validate_email
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mnopi.models import User, PageVisited, Search, ClientSession, CategorizedDomain, Client
from mnopi import constants
from mnopi import opendns
from mnopi import models_mongo


#TODO: poner un borrado de sessions de vez en cuando?

def get_user_id_from_resource(user_resource):
    return user_resource.rsplit("/", 2)[-2]

class MnopiUserAuthentication(Authentication):
    """
    Basic API authentication which requires the user resource and the session token in the header

    Users are able to access or modify only their data
    """

    def is_authenticated(self, request, **kwargs):

        if not 'HTTP_SESSION_TOKEN' in request.META:
            return False

        session_token = request.META['HTTP_SESSION_TOKEN']

        try:
            session = ClientSession.objects.get(session_token=session_token)
        except ClientSession.DoesNotExist:
            return False

        if session.expiration_time < datetime.datetime.utcnow().replace(tzinfo=utc):
            session.delete()
            return False

        request.user = session.user

        return True

class UserObjectsOnlyAuthorization(Authorization):
    """
    Allows users to read or create only their data

    Update and deletions unauthorized
    """
    def read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user)

    def read_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def create_list(self, object_list, bundle):
        return bundle.request.user == UserResource().get_via_uri(bundle.data['user'])

    def create_detail(self, object_list, bundle):
        return bundle.request.user == UserResource().get_via_uri(bundle.data['user'])

    def update_list(self, object_list, bundle):
        raise Unauthorized("Update not possible")

    def update_detail(self, object_list, bundle):
        raise Unauthorized("Update not possible")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Deletion not possible")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Deletion not possible")

class UserCreationValidation(Validation):

    def is_valid(self, bundle, request=None):

        errors = {}
        if 'username' not in bundle.data or bundle.data['username'] == "":
            errors['username'] = "Not specified"
        if 'password' not in bundle.data or bundle.data['password'] == "":
            errors['password'] = "Not specified"
        if 'email' not in bundle.data or bundle.data['email'] == "":
            errors['email'] = "Not specified"
        if errors:
            return errors

        if not constants.USERNAME_MIN_LENGTH <= len(bundle.data['username']) <= constants.USERNAME_MAX_LENGTH:
            errors['username'] = "Username too short or too long"
        if not constants.PASS_MIN_LENGTH <= len(bundle.data['password']) <= constants.PASS_MAX_LENGTH:
            errors['password'] = "Password too short or too long"
        if len(bundle.data['email']) > constants.EMAIL_MAX_LENGTH:
            errors['email'] = "Too long an email"
        if errors:
            return errors


        if not bundle.data['username'].isalnum():
            errors['username'] = "Username characters must be alphanumeric"
            return errors

        try:
            validate_email(bundle.data['email'])
        except ValidationError, e:
            errors['email'] = "Not an email address"
            return errors

        # All previous validations should have been performed by the client, the server won't provide
        # any additional details
        #TODO: maybe from here this should raise a different response and not a bad request
        if User.objects.filter(username=bundle.data['username']).count() != 0:
            errors['username'] = "Username already exists"
            return errors

        if User.objects.filter(email=bundle.data['email']).count() != 0:
            errors['email'] = "Email already registered"

        return errors

class UserResource(ModelResource):

    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        validation = UserCreationValidation()
        #fields = ['username'] #TODO: Restrict in production
        allowed_methods = ['get', 'post']
        filtering = {
            "username": ('exact') #TODO : Quitar si es posible
        }

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('sign_up'), name='api_sign_up'),
            url(r"^(?P<resource_name>%s)/login%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('login'), name="api_login"),
            url(r'^(?P<resource_name>%s)/logout%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('logout'), name='api_logout')
            ]

    def is_valid_registration(self, bundle):
        errors = self._meta.validation.is_valid(bundle, bundle.request)

        if errors:
            bundle.errors = {'result': 'ERR',
                             'reason': 'BAD_PARAMETERS',
                             'erroneous_parameters': errors}

            return False

        return True

    def response_err(self, request, reason):
        return self.create_response(request, {
                'result': "ERR",
                'reason': reason
        })

    def sign_up(self, request, **kwargs):

        self.method_check(request, allowed=['post'])

        data = self.deserialize(request, request.body)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(data), request=request)
        self.is_valid_registration(bundle)
        if bundle.errors:
            raise ImmediateHttpResponse(response=self.error_response(bundle.request, bundle.errors))

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        User.objects.create_user(username=username, password=password, email=email)

        return self.create_response(request, '', HttpCreated)


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
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = PageVisited.objects.all()
        authentication = MnopiUserAuthentication()
        authorization = UserObjectsOnlyAuthorization()
        validation = PageVisitedValidation()
        resource_name = 'page_visited'
        allowed_methods = ['post', 'get']
        excludes = ['id', 'html_ref', 'user']
        filtering = {
            'date': ALL
        }
        ordering = {
            'date': ALL
        }

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
        return [url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/categories%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('page_categories'), name="page_categories")]

    def dispatch(self, request_type, request, **kwargs):
        """
        Overriden to control post behaviour
        """
        request_method = request.method.lower()
        if request_method == 'post' and 'post' in self._meta.allowed_methods:
            return self.add_page_visited(request, **kwargs)
        else:
            return super(PageVisitedResource, self).dispatch(request_type, request, **kwargs)

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
        session_token = request.META['HTTP_SESSION_TOKEN']

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

    def page_categories(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)

        # Tastypie is so great and easy for authorization...
        bundle = self.build_bundle(request=request)
        try:
            obj = self.cached_obj_get(bundle=bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        bundle = self.build_bundle(obj=obj, request=request)
        self.authorized_read_detail(None, bundle)

        page = PageVisited.objects.get(id=kwargs['pk'])
        return self.create_response(request, [cat.name for cat in page.domain.categories.all()])


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
        authorization = UserObjectsOnlyAuthorization()
        validation = SearchQueryValidation()
        resource_name = 'search_query'
        allowed_methods = ['post', 'get', 'patch', 'put']
        excludes = ['id']
        filtering = {
            'search_query': ALL,
            'date': ALL
        }
        ordering = {
            'date': ALL
        }

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
        bundle.obj.client = ClientSession.objects.get(
            session_token=bundle.request.META['HTTP_SESSION_TOKEN']).client

        return bundle