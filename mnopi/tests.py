from models import UserCategory, User, CategorizedDomain, UserCategorization, PageVisited, Search, ClientSession, Client
from api import UserResource
import opendns
import constants

from tastypie.test import ResourceTestCase
from django.test import TestCase, TransactionTestCase

from pymongo import MongoClient
import datetime
import json

API_URI = {
    'user': '/api/v1/user/',
    'signup': '/api/v1/user/',
    'login': '/api/v1/user/login/',
    'page_visited': '/api/v1/page_visited/',
    'html': '/api/v1/page_visited/html/',
    'search_query': '/api/v1/search_query/'
}

class CategorizableResourceTest(TestCase):
    """ Test case with OpenDNS categories loaded """

    def setUp(self):
        super(CategorizableResourceTest, self).setUp()
        for category in opendns.CATEGORIES.values():
            UserCategory.objects.create(name=category, taxonomy="opendns")

class AuthenticableResourceTest(ResourceTestCase):
    """ Test case with authentication capabilities """

    def setUp(self):
        super(AuthenticableResourceTest, self).setUp()

        # Create a user
        self.username = 'alfredo'
        self.password = '1aragon1'
        self.user = User.objects.create_user(self.username, 'alfredo@example.com', self.password)
        self.client = Client.objects.create(client_name="test-client")
        self.client_name = self.client.client_name

    def perform_login(self, username=None, key=None, renew=False, client=None):
        """
        If defaulted to none, correct login parameters will be set
        """

        if username is None:
            username = self.username
        if key is None:
            key = self.password
        if client is None:
            client = self.client_name
        if renew is None:
            login_data = {
                'username': username,
                'key': key,
                'client': client
            }
        else:
            login_data = {
                'username': username,
                'key': key,
                'renew': renew,
                'client': client
        }
        resp = self.api_client.post(API_URI['login'], data=login_data, format='json')
        deserialized_resp = self.deserialize(resp)

        if deserialized_resp['result'] == "OK":
            self.user_resource = deserialized_resp['user_resource']
            self.session_token = deserialized_resp['session_token']

        return resp


class ModelsMongoTest(TestCase):
    """ Test case that initializes and destroys a mongodb database for testing purposes """

    from mnopi import models_mongo as test_mongo

    @classmethod
    def setUpClass(cls):
        super(ModelsMongoTest, cls).setUpClass()
        cls.test_mongo.db = MongoClient().mnopi_test

    @classmethod
    def tearDownClass(cls):
        super(ModelsMongoTest, cls).tearDownClass()
        cls.test_mongo.db.drop()

class UserRegistrationTest(ResourceTestCase):
    """ Sign up service tests """

    def user_registration(self, username, password, email):

        user_data = {
            'username': username,
            'password': password,
            'email': email
        }
        resp = self.api_client.post(API_URI['signup'], data=user_data, format='json')
        return resp

    #######################
    ## Parameters checks
    #######################
    def test_no_username(self):
        resp = self.user_registration(username="",
                                      password="1234567890",
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['username'])

    def test_no_password(self):
        resp = self.user_registration(username="amparo",
                                      password="",
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['password'])

    def test_no_email(self):
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email="")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['email'])

    ########################
    ## Validation checks
    ########################
    def test_password_too_short(self):
        resp = self.user_registration(username="amparo",
                                      password="1" * (constants.PASS_MIN_LENGTH - 1),
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['password'])

    def test_password_too_long(self):
        LONG_PASSWORD = "1" * constants.PASS_MAX_LENGTH + "1"
        resp = self.user_registration(username="amparo",
                                      password=LONG_PASSWORD,
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['password'])

    def test_email_is_email_1(self):
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email="pringao")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['email'])

    def test_email_is_email_2(self):
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email="pringao@lolazo")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['email'])

    def test_email_is_email_3(self):
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email="@juasjuas.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['email'])

    def test_email_too_long(self):
        LONG_EMAIL = "a" * (constants.EMAIL_MAX_LENGTH + 1 - 6) + "@a.com"
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email=LONG_EMAIL)
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['email'])

    def test_username_is_alphanumeric(self):
        resp = self.user_registration(username="amparo@gmail.com",
                                      password="1234567890",
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['username'])

    def test_username_too_short(self):
        resp = self.user_registration(username="a" * (constants.USERNAME_MIN_LENGTH - 1),
                                      password="1234567890",
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['username'])

    def test_username_too_long(self):
        resp = self.user_registration(username="a" * (constants.USERNAME_MAX_LENGTH + 1),
                                      password="1234567890",
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['username'])

    def test_username_already_exists(self):
        User.objects.create(username="amparo", password="1234567890", email="amparo@gmail.com")
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email="amparito@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['username'])

    def test_email_already_exists(self):
        User.objects.create(username="amparo", password="1234567890", email="amparo@gmail.com")
        resp = self.user_registration(username="superamparo",
                                      password="1234567890",
                                      email="amparo@gmail.com")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['email'])

    ######################
    ## Behavior tests
    ######################
    def test_registration_successful(self):
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email="amparo@gmail.com")
        self.assertHttpCreated(resp)

        self.assertEqual(User.objects.filter(username="amparo", email="amparo@gmail.com").count(), 1)

    def test_password_hashed(self):
        resp = self.user_registration(username="amparo",
                                      password="1234567890",
                                      email="amparo@gmail.com")
        self.assertHttpCreated(resp)

        self.assertEqual(User.objects.filter(password="1234567890").count(), 0)

class UserLoginTest(AuthenticableResourceTest):
    """ Login service tests """

    def setUp(self):
        super(UserLoginTest, self).setUp()

        # Create an already opened session
        self.last_session_token = self.user.new_session(self.client)

        # Create an expired session
        self.expired_session_token = self.user.new_session(self.client)
        expired_session = ClientSession.objects.get(session_token=self.expired_session_token)
        expired_session.expiration_time -= datetime.timedelta(days=constants.PLUGIN_SESSION_EXPIRY_DAYS + 1)
        expired_session.save()

        # Create a not allowed client
        self.disallowed_client = Client.objects.create(client_name="not-allowed", allowed=False).client_name

    def test_correct_password_login(self):
        resp = self.perform_login(username=self.username,
                                  key=self.password,
                                  renew=False)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'session_token', 'user_resource'])
        self.assertEqual(deserialized_resp['result'], 'OK')
        self.assertEqual(deserialized_resp['user_resource'], API_URI['user'] + '%s/' % (self.user.id))

        # Check that a new session has been created
        self.assertEqual(ClientSession.objects.count(), 3)

    def test_correct_renew_not_specified(self):
        # Renew parameter should not be important if not True
        resp = self.perform_login(username=self.username,
                                  key=self.password)

        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'session_token', 'user_resource'])
        self.assertEqual(deserialized_resp['result'], 'OK')
        self.assertEqual(deserialized_resp['user_resource'], API_URI['user'] + '%s/' % (self.user.id))

        # Check that a new session has been created
        self.assertEqual(ClientSession.objects.count(), 3)

    def test_correct_renew_login(self):
        resp = self.perform_login(username=self.username,
                                  key=self.last_session_token,
                                  renew=True)

        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'session_token', 'user_resource'])
        self.assertEqual(deserialized_resp['result'], 'OK')
        self.assertNotEqual(deserialized_resp['session_token'], self.last_session_token)
        self.assertEqual(deserialized_resp['user_resource'], API_URI['user'] + '%s/' % (self.user.id))

    def test_impossible_to_renew_again(self):
        resp = self.perform_login(username=self.username,
                                  key=self.last_session_token,
                                  renew=True)
        self.assertValidJSONResponse(resp)

        new_resp = self.perform_login(username=self.username,
                                      key=self.last_session_token,
                                      renew=True)
        self.assertValidJSONResponse(resp)

        des_resp = self.deserialize(new_resp);
        self.assertEqual(des_resp, {
            'result': 'ERR',
            'reason': "UNEXPECTED_SESSION"
        })

    def test_correct_password_login_plus_correct_renew_session(self):
        resp = self.perform_login(username=self.username,
                                  key=self.password,
                                  renew=False)
        deserialized_resp = self.deserialize(resp)

        new_resp = self.perform_login(username=self.username,
                                      key=deserialized_resp['session_token'],
                                      renew=True)
        self.assertValidJSONResponse(resp)

        deserialized_new_resp = self.deserialize(new_resp)
        self.assertKeys(deserialized_resp, ['result', 'session_token', 'user_resource'])
        self.assertKeys(deserialized_new_resp, ['result', 'session_token', 'user_resource'])
        self.assertEqual(deserialized_new_resp['result'], 'OK')
        self.assertNotEqual(deserialized_resp['session_token'], deserialized_new_resp['session_token'])
        self.assertEqual(deserialized_resp['user_resource'], API_URI['user'] + '%s/' % (self.user.id))

    def test_incorrect_renew_login(self):
        resp = self.perform_login(username="pepito",
                                  key=self.last_session_token,
                                  renew=True)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "INCORRECT_USER_PASSWORD"
        })

    def test_incorrect_token_renew_session_login(self):
        resp = self.perform_login(username=self.username,
                                  key="1111",
                                  renew=True)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "UNEXPECTED_SESSION"
        })

    def test_expired_session_renew_login(self):
        resp = self.perform_login(username=self.username,
                                  key=self.expired_session_token,
                                  renew=True)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "UNEXPECTED_SESSION"
        })

    def test_client_outdated_password_login(self):
        resp = self.perform_login(username=self.username,
                                  key=self.password,
                                  renew=False,
                                  client="dummyversion")
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "CLIENT_ERROR"
        })

    def test_client_outdated_renew_login(self):
        resp = self.perform_login(username=self.username,
                                  key=self.last_session_token,
                                  renew=False,
                                  client=self.disallowed_client)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "CLIENT_OUTDATED"
        })

    def test_client_error_renew_login(self):
        resp = self.perform_login(username=self.username,
                                  key=self.last_session_token,
                                  renew=True,
                                  client="dummyversion")
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "CLIENT_ERROR"
        })

    def test_client_outdated_renew_login(self):
        resp = self.perform_login(username=self.username,
                                  key=self.last_session_token,
                                  renew=True,
                                  client=self.disallowed_client)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "CLIENT_OUTDATED"
        })

    def test_password_error_password_login(self):
        resp = self.perform_login(username=self.username,
                                  key="abcdefghi",
                                  renew=False)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "INCORRECT_USER_PASSWORD"
        })

    def test_user_error_password_login(self):
        resp = self.perform_login(username="pepito",
                                  key=self.password,
                                  renew=False)
        self.assertValidJSONResponse(resp)

        deserialized_resp = self.deserialize(resp)
        self.assertKeys(deserialized_resp, ['result', 'reason'])
        self.assertEqual(deserialized_resp, {
            'result': 'ERR',
            'reason': "INCORRECT_USER_PASSWORD"
        })


class HtmlVisitedResourceTest(AuthenticableResourceTest, ModelsMongoTest):
    """ Html visited service tests """

    def setUp(self):
        super(HtmlVisitedResourceTest, self).setUp()
        self.perform_login()


    def perform_html_visited(self, url, html_code, user_resource=None, session_token=None):

        if user_resource is None:
            user_resource = self.user_resource
        if session_token is None:
            session_token = self.session_token

        html_visited_data = {
            'user_resource': user_resource,
            'url': url,
            'html_code': html_code
        }
        return self.api_client.post(API_URI['html'], data=html_visited_data,
                                    format='json', HTTP_SESSION_TOKEN=session_token)

    #TODO: SEGUIR POR AQUI

class PageVisitedResourceTest(AuthenticableResourceTest, CategorizableResourceTest):
    """
    Page visited service tests

    Avoid doing many calls to perform_page_visited as they are very slow (query to opendns)
    """

    def setUp(self):
        super(PageVisitedResourceTest, self).setUp()
        self.perform_login()

    def perform_page_visited(self, url, html_code=None, date="2014-01-01 00:00:00",
                             user_resource=None, session_token=None):

        if user_resource is None:
            user_resource = self.user_resource
        if session_token is None:
            session_token = self.session_token

        if html_code:
            page_visited_data = {
                'user': user_resource,
                'url': url,
                'html_code': html_code,
                'date': date
            }
        else:
            page_visited_data = {
                'user': user_resource,
                'url': url,
                'date': date
            }

        return self.api_client.post(API_URI['page_visited'], data=page_visited_data,
                                    format='json', HTTP_SESSION_TOKEN=session_token)

    ######################
    # Parameters checks
    ######################

    #TODO: Add Authorization

    # def test_no_user(self):
    #     other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
    #     other_user_resource = UserResource().get_resource_uri(other_user)
    #
    #     resp = self.perform_page_visited(url="http://www.lol.com",
    #                                      user_resource=other_user_resource,
    #                                      session_token=self.session_token)
    #     self.assertHttpUnauthorized(resp)

    def test_invalid_session_token(self):
        resp = self.perform_page_visited(url="http://www.lol.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token + "a")
        self.assertHttpUnauthorized(resp)

    def test_no_url(self):
        resp = self.perform_page_visited(url="")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['url'])

    def test_no_date(self):
        resp = self.perform_page_visited(url="http://molamazo.com", date="")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['date'])


    ######################
    # Validation checks
    ######################
    def test_invalid_url_1(self):
        resp = self.perform_page_visited(url="1234567890")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['url'])

    def test_invalid_url_2(self):
        resp = self.perform_page_visited(url="www.elmundo.es") # Lacks protocol
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['url'])

    def test_invalid_date(self):
        resp = self.perform_page_visited(url="http://loco.com", date="2014-89-34 00:00:00")
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['date'])

    ######################
    # Behaviour tests
    ######################
    def test_add_page(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpCreated(resp)

        num_pages = PageVisited.objects.filter(user=self.user, page_visited="http://www.lol.com").count()
        self.assertEqual(num_pages, 1)

        resp = self.perform_page_visited(url="http://lol.com")
        self.assertHttpCreated(resp)

        num_pages = PageVisited.objects.filter(user=self.user).count()
        self.assertEqual(num_pages, 2)

    def test_two_domains_added(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpCreated(resp)

        domains = CategorizedDomain.objects.filter(domain="www.lol.com").count()
        self.assertEqual(domains, 1)

        resp = self.perform_page_visited(url="http://lol.com")
        self.assertHttpCreated(resp)

        domains = CategorizedDomain.objects.filter(domain="lol.com").count()
        self.assertEqual(domains, 1)

    def test_domains_repeated(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpCreated(resp)

        resp = self.perform_page_visited(url="http://www.lol.com/2")
        self.assertHttpCreated(resp)

        domains = CategorizedDomain.objects.filter(domain="www.lol.com").count()
        self.assertEqual(domains, 1)

    def test_categorized_domain(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpCreated(resp)

        domain = CategorizedDomain.objects.get(domain="www.lol.com")
        self.assertEqual([x.name for x in domain.categories.all()], ['Humor'])

    def test_categorized_domain_multiple_categories(self):
        resp = self.perform_page_visited(url="http://stackoverflow.com")
        self.assertHttpCreated(resp)

        domain = CategorizedDomain.objects.get(domain="stackoverflow.com")
        self.assertEqual(set([x.name for x in domain.categories.all()]),
                         set(['Software/Technology', 'Research/Reference', 'Forums/Message boards']))

    def test_user_categorization(self):
        resp = self.perform_page_visited(url="http://stackoverflow.com")
        self.assertHttpCreated(resp)

        categories = CategorizedDomain.objects.get(domain="stackoverflow.com").categories.all()
        for cat in categories:
            user_cat = UserCategorization.objects.get(user=self.user, category=cat)
            self.assertEqual(user_cat.weigh, 1)

        resp = self.perform_page_visited(url="http://stackoverflow.com")
        self.assertHttpCreated(resp)

        categories = CategorizedDomain.objects.get(domain="stackoverflow.com").categories.all()
        for cat in categories:
            user_cat = UserCategorization.objects.get(user=self.user, category=cat)
            self.assertEqual(user_cat.weigh, 2)

            # TODO: More tests

class SearchQueryResourceTest(AuthenticableResourceTest):
    """ Test case for search engines queries """

    def setUp(self):
        super(SearchQueryResourceTest, self).setUp()
        self.perform_login()

    def search_query(self, user_resource, search_query, search_results,
                     date="2014-01-01 00:00:00"):

        if user_resource is None:
            user_resource = self.user_resource

        return {
            'user': user_resource,
            'search_query': search_query,
            'search_results': search_results,
            'date': date
        }

    def perform_search_query(self, search_query, search_results, date="2014-01-01 00:00:00",
                             user_resource=None, session_token=None):

        if user_resource is None:
            user_resource = self.user_resource
        if session_token is None:
            session_token = self.session_token

        search_query_data = self.search_query(user_resource, search_query, search_results, date)
        return self.api_client.post(API_URI['search_query'], data=search_query_data,
                                    format='json', HTTP_SESSION_TOKEN=session_token)

    def get_search_queries(self, session_token=None):

        if session_token is None:
            session_token = self.session_token

        return self.api_client.get(API_URI['search_query'], format='json',
                                   HTTP_SESSION_TOKEN=session_token)

    def multiple_search_queries(self, session_token, *queries):

        data = {"objects": list(queries)}

        return self.api_client.patch(API_URI['search_query'], data=data, format='json',
                                     HTTP_SESSION_TOKEN=session_token)

    ######################
    # Security tests
    ######################
    def test_post_bad_session_token(self):
        resp = self.perform_search_query(search_query="lolazos",
                                         search_results="http://lol.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token+"a")
        self.assertHttpUnauthorized(resp)

    def test_user_post_to_other_user(self):
        other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
        other_user_resource = UserResource().get_resource_uri(other_user)

        resp = self.perform_search_query(search_query="lolazos",
                                         search_results="http://lol.com",
                                         user_resource=other_user_resource,
                                         session_token=self.session_token)
        self.assertHttpUnauthorized(resp)

    def test_get_without_session(self):
        resp = self.get_search_queries(session_token="")
        self.assertHttpUnauthorized(resp)

    def test_get_other_user_info(self):
        other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
        other_user_token = other_user.new_session(self.client)
        other_user_resource = UserResource().get_resource_uri(other_user)

        # Other user adds search query
        resp = self.perform_search_query(search_query="lolazos",
                                         search_results="http://lol.com",
                                         user_resource=other_user_resource,
                                         session_token=other_user_token)
        self.assertHttpCreated(resp)

        # Our user adds search query
        resp = self.perform_search_query(search_query="lolazos",
                                         search_results="http://lol.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token)
        self.assertHttpCreated(resp)

        resp = self.get_search_queries()
        deserialized_resp = self.deserialize(resp)

        # We should see only our query
        self.assertEqual(deserialized_resp["meta"]["total_count"], 1)

    def test_patch_no_session(self):
        search_query = self.search_query(user_resource=self.user_resource,
                                         search_query="Carrozas de papel",
                                         search_results="http://unamierda.com")

        resp = self.multiple_search_queries("", search_query)
        self.assertHttpUnauthorized(resp)

    def test_patch_other_user_info(self):
        other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
        other_user_resource = UserResource().get_resource_uri(other_user)

        my_search_query = self.search_query(user_resource=self.user_resource,
                                            search_query="Carrozas de papel",
                                            search_results="http://unamierda.com")

        other_search_query = self.search_query(user_resource=other_user_resource,
                                               search_query="Carrozas de papel",
                                               search_results="http://unamierda.com")

        resp = self.multiple_search_queries(self.session_token, my_search_query, other_search_query)
        self.assertHttpUnauthorized(resp)


    ######################
    # Parameters checks
    ######################
    #TODO: don't give error with lack of parameters
    # def test_user_empty(self):
    #     resp = self.perform_search_query(search_query="lolazos",
    #                                      search_results="http://lol.com",
    #                                      user_resource="",
    #                                      session_token=self.session_token)
    #     self.assertHttpUnauthorized(resp)

    def test_no_query(self):
        resp = self.perform_search_query(search_query="",
                                         search_results="http://lol.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token)
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['search_query'])

    def test_no_search_results(self):
        resp = self.perform_search_query(search_query="lolazo",
                                         search_results="",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token)
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['search_results'])

    def test_no_date(self):
        resp = self.perform_search_query(search_query="lolazo",
                                         search_results="http://www.lol.com",
                                         user_resource=self.user_resource,
                                         date="",
                                         session_token=self.session_token)
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['date'])

    # Multiple posts tests are reduced to these tests as they are considered normal post

    ######################
    # Validation checks
    ######################
    def test_date_bad_format(self):
        resp = self.perform_search_query(search_query="lolazo",
                                         search_results="http://www.lol.com",
                                         user_resource=self.user_resource,
                                         date="2005/23/23 00:23:98",
                                         session_token=self.session_token)
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['date'])

    # TODO: More checks to date should be done

    def test_search_results_not_url(self):
        resp = self.perform_search_query(search_query="lolazo",
                                         search_results="jajaja.lol.com",
                                         user_resource=self.user_resource,
                                         date="2014-01-01 00:10:10",
                                         session_token=self.session_token)
        self.assertHttpBadRequest(resp)
        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data['reason'], "BAD_PARAMETERS")
        self.assertKeys(resp_data['erroneous_parameters'], ['search_results'])


    ######################
    # Behaviour checks
    ######################
    def test_search_done(self):
        resp = self.perform_search_query(search_query="lolazo",
                                         search_results="http://lol.com")
        self.assertHttpCreated(resp)

        # Check that the search queary has been saved
        searches = Search.objects.filter(search_query="lolazo", search_results="http://lol.com",
                                      user=self.user).count()
        self.assertEqual(searches, 1)

        # Check that the client was correctly assigned
        search = Search.objects.get(search_query="lolazo", search_results="http://lol.com", user=self.user)
        self.assertEqual(search.client, self.client)

    def test_get_search_queries(self):
        resp = self.perform_search_query(search_query="Lolazo 1",
                                         search_results="http://lol.com")
        self.assertHttpCreated(resp)

        resp = self.perform_search_query(search_query="Lolazo 2",
                                         search_results="http://lol2.com")
        self.assertHttpCreated(resp)

        resp = self.perform_search_query(search_query="Lolazo 3",
                                         search_results="http://lol3.com")
        self.assertHttpCreated(resp)

        resp = self.perform_search_query(search_query="Lolazo 4",
                                         search_results="http://lol4.com")
        self.assertHttpCreated(resp)

        resp = self.get_search_queries()
        deserialized_resp = self.deserialize(resp)

        self.assertEqual(deserialized_resp["meta"]["total_count"], 4)
        self.assertEqual(len(deserialized_resp["objects"]), 4)

    def test_multiple_searches(self):
        search_query_1 = self.search_query(user_resource=self.user_resource,
                                           search_query="Carrozas de papel",
                                           search_results="http://unamierda.com")

        search_query_2 = self.search_query(user_resource=self.user_resource,
                                           search_query="Carrozas de papel 2",
                                           search_results="http://unamierda.com")

        search_query_3 = self.search_query(user_resource=self.user_resource,
                                           search_query="Carrozas de papel 3",
                                           search_results="http://unamierda.com")

        resp = self.multiple_search_queries(self.session_token, search_query_1, search_query_2,
                                            search_query_3)
        self.assertHttpAccepted(resp)
        self.assertEqual(Search.objects.all().count(), 3)

    def test_multiple_searches_none_saved_if_one_fails(self):
        search_query_1 = self.search_query(user_resource=self.user_resource,
                                           search_query="Carrozas de papel 1",
                                           search_results="http://unamierda.com")

        # Error in this query
        search_query_2 = self.search_query(user_resource=self.user_resource,
                                           search_query="Carrozas de papel 2",
                                           search_results="http://unamierda.com")

        search_query_3 = self.search_query(user_resource=self.user_resource,
                                           search_query="",
                                           search_results="http://unamierda.com")

        resp = self.multiple_search_queries(self.session_token, search_query_1, search_query_2,
                                            search_query_3)
        self.assertHttpBadRequest(resp)

        # It is not possible to test correct rollback of the database as TransactionTestCase
        # would be needed. They are currently not supported by TastyPie tests

