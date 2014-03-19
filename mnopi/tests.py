from models import UserCategory, User, CategorizedDomain, UserCategorization, PageVisited, Search, ClientSession, Client
import opendns
import constants

from tastypie.test import ResourceTestCase
from django.test import TestCase

from pymongo import MongoClient
import datetime
import json

API_URI = {
    'user': '/api/v1/user/',
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




class UserResourceTest(AuthenticableResourceTest):
    """ Login service tests """

    def setUp(self):
        super(UserResourceTest, self).setUp()

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


class PageVisitedResourceTest(AuthenticableResourceTest, CategorizableResourceTest):
    """
    Page visited service tests

    Avoid doing many calls to perform_page_visited as they are very slow (query to opendns)
    """

    def setUp(self):
        super(PageVisitedResourceTest, self).setUp()
        self.perform_login()

    def perform_page_visited(self, url, user_resource=None, session_token=None):

        if user_resource is None:
            user_resource = self.user_resource
        if session_token is None:
            session_token = self.session_token

        page_visited_data = {
            'user_resource': user_resource,
            'session_token': session_token,
            'url': url
        }
        return self.api_client.post(API_URI['page_visited'], data=page_visited_data, format='json')

    def test_no_user(self):
        resp = self.perform_page_visited(url="http://www.lol.com",
                                         user_resource="/api/v1/user/18/",
                                         session_token=self.session_token)
        self.assertHttpUnauthorized(resp)

    def test_invalid_session_token(self):
        resp = self.perform_page_visited(url="http://www.lol.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token + "a")
        self.assertHttpUnauthorized(resp)

    def test_no_url(self):
        resp = self.perform_page_visited(url="")
        self.assertHttpBadRequest(resp)

    def test_add_page_added(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpOK(resp)

        num_pages = PageVisited.objects.filter(user=self.user, page_visited="http://www.lol.com").count()
        self.assertEqual(num_pages, 1)

        resp = self.perform_page_visited(url="http://lol.com")
        self.assertHttpOK(resp)

        num_pages = PageVisited.objects.filter(user=self.user).count()
        self.assertEqual(num_pages, 2)

    def test_two_domains_added(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpOK(resp)

        domains = CategorizedDomain.objects.filter(domain="www.lol.com").count()
        self.assertEqual(domains, 1)

        resp = self.perform_page_visited(url="http://lol.com")
        self.assertHttpOK(resp)

        domains = CategorizedDomain.objects.filter(domain="lol.com").count()
        self.assertEqual(domains, 1)

    def test_domains_repeated(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpOK(resp)

        resp = self.perform_page_visited(url="http://www.lol.com/2")
        self.assertHttpOK(resp)

        domains = CategorizedDomain.objects.filter(domain="www.lol.com").count()
        self.assertEqual(domains, 1)

    def test_categorized_domain(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpOK(resp)

        domain = CategorizedDomain.objects.get(domain="www.lol.com")
        self.assertEqual([x.name for x in domain.categories.all()], ['Humor'])

    def test_categorized_domain_multiple_categories(self):
        resp = self.perform_page_visited(url="http://stackoverflow.com")
        self.assertHttpOK(resp)

        domain = CategorizedDomain.objects.get(domain="stackoverflow.com")
        self.assertEqual(set([x.name for x in domain.categories.all()]),
                         set(['Software/Technology', 'Research/Reference', 'Forums/Message boards']))

    def test_user_categorization(self):
        resp = self.perform_page_visited(url="http://stackoverflow.com")
        self.assertHttpOK(resp)

        categories = CategorizedDomain.objects.get(domain="stackoverflow.com").categories.all()
        for cat in categories:
            user_cat = UserCategorization.objects.get(user=self.user, category=cat)
            self.assertEqual(user_cat.weigh, 1)

        resp = self.perform_page_visited(url="http://stackoverflow.com")
        self.assertHttpOK(resp)

        categories = CategorizedDomain.objects.get(domain="stackoverflow.com").categories.all()
        for cat in categories:
            user_cat = UserCategorization.objects.get(user=self.user, category=cat)
            self.assertEqual(user_cat.weigh, 2)

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
            'session_token': session_token,
            'url': url,
            'html_code': html_code
        }
        return self.api_client.post(API_URI['html'], data=html_visited_data, format='json')

    #TODO: SEGUIR PRO AQUI

class SearchQueryResourceTest(AuthenticableResourceTest):
    """ Test case for search engines queries """

    def setUp(self):
        super(SearchQueryResourceTest, self).setUp()
        self.perform_login()

    def perform_search_query(self, search_query, search_results, date="2014-01-01 00:00:00",
                             user_resource=None, session_token=None):

        if user_resource is None:
            user_resource = self.user_resource
        if session_token is None:
            session_token = self.session_token

        search_query_data = {
            'user': user_resource,
            'session_token': session_token,
            'search_query': search_query,
            'search_results': search_results,
            'date': date
        }
        return self.api_client.post(API_URI['search_query'], data=search_query_data, format='json')

    ######################
    # Parameters checks
    ######################
    def test_user_empty(self):
        resp = self.perform_search_query(search_query="lolazos",
                                         search_results="http://lol.com",
                                         user_resource="",
                                         session_token=self.session_token)
        self.assertHttpUnauthorized(resp)

    def test_not_authenticated_user(self):
        resp = self.perform_search_query(search_query="lolazos",
                                         search_results="http://lol.com",
                                         user_resource="/api/v1/user/18/",
                                         session_token=self.session_token)
        self.assertHttpUnauthorized(resp)

    def test_session_token(self):
        resp = self.perform_search_query(search_query="lolazos",
                                         search_results="http://lol.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token+"a")
        self.assertHttpUnauthorized(resp)

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