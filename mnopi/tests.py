# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management import call_command
from models import UserCategory, User, CategorizedDomain, UserCategorization, PageVisited, Search, ClientSession, Client
from api import UserResource
import opendns
import constants
import management.commands.process_keywords
from tastypie.test import ResourceTestCase
from django.test import TestCase, TransactionTestCase

from pymongo import MongoClient, Connection
import datetime
import json

API_URI = {
    'user': '/api/v1/user/',
    'signup': '/api/v1/user/',
    'login': '/api/v1/user/login/',
    'page_visited': '/api/v1/page_visited/',
    'page_categories': '/api/v1/page_visited/%s/categories/',
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

    def tearDown(self):
        super(ModelsMongoTest, self).tearDown()
        self.test_mongo.db.htmlVisited.drop()
        self.test_mongo.db.userKeywords.drop()

    @classmethod
    def tearDownClass(cls):
        super(ModelsMongoTest, cls).tearDownClass()
        c = Connection()
        c.drop_database("mnopi_test")

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


    def perform_html_visited(self, url, html_code, date, user_resource=None, session_token=None):

        if user_resource is None:
            user_resource = self.user_resource
        if session_token is None:
            session_token = self.session_token

        html_visited_data = {
            'user': user_resource,
            'url': url,
            'html_code': html_code,
            'date': date
        }
        return self.api_client.post(API_URI['html'], data=html_visited_data,
                                    format='json', HTTP_SESSION_TOKEN=session_token)

    def test_html_inserted(self):
        # TODO: Comprobar la fecha que se mete
        self.perform_html_visited(url= "http://molamazo.com",
                                  html_code= "<hmtl><head></head></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        id = collection.find({},{"_id" : 1})[0]["_id"]
        html = collection.find()[0]["html_code"]
        date = collection.find()[0]["date"]
        page = collection.find()[0]["page_visited"]
        self.assertEqual(html, "<hmtl><head></head></html>")
        self.assertEqual(page, "http://molamazo.com")
        self.assertEquals(PageVisited.objects.filter(html_ref=id).count(),1)

    def test_html_metadata_words(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "<meta name=\"keywords\" content=\"Noticias de última\">"
                                             "<title>Noticias de última</title></head><body><a>Hola, Noticias</a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        metadata_words = collection.find()[0]["keywords_freq"]["metadata"]
        a = metadata_words["noticias"]
        b = metadata_words["última"]
        self.assertEquals(a,3)
        self.assertEquals(b,3)

    def test_clean_invalid_words(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>Hola 1, s, " + "d" * (constants.WORD_MAX_LENGTH+1) +" </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        valid_words = collection.find()[0]["keywords_freq"]["text"]
        long_word = "d" * (constants.WORD_MAX_LENGTH+1)
        self.assertNotIn("1", valid_words)
        self.assertNotIn("s", valid_words)
        self.assertNotIn(long_word, valid_words)

    def test_html_text_words(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>Hola, Noticias Hola </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        text_words = collection.find()[0]["keywords_freq"]["text"]
        self.assertEquals(text_words["noticias"],1)
        self.assertEquals(text_words["hola"],2)

    def test_html_title(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "<title>Noticias de última</title></head><body><a>Hola, Noticias Hola </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        title = collection.find()[0]["properties"]["title"]
        self.assertEquals(title,"Noticias de última")

    def test_html_keywords(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "<meta name=\"keywords\" content=\"estas son las keywords\"></head>"
                                             "<body><a>Hola, Noticias Hola </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        keywords = collection.find()[0]["properties"]["keywords"]
        self.assertEquals(keywords,"estas son las keywords")

    def test_html_description(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "<meta name=\"keywords\" content=\"estas son las keywords\"></head>"
                                             "<body><a>Hola, Noticias Hola </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        description = collection.find()[0]["properties"]["description"]
        self.assertEquals(description,"Noticias de última")

    def test_html_clean_punctuation(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>Hola, Noti.cias H-ola </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        valid_words = collection.find()[0]["keywords_freq"]["text"]
        self.assertNotIn("h-ola", valid_words)
        self.assertNotIn("noti.cias", valid_words)
        self.assertNotIn("hola,", valid_words)
        self.assertEquals(valid_words["hola"],2)
        self.assertEquals(valid_words["noticias"],1)

    def test_html_lowercase(self):
        self.perform_html_visited(url= "http://mola.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>Hola Noticias Hola hola </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        valid_words = collection.find()[0]["keywords_freq"]["text"]
        self.assertNotIn("Hola", valid_words)
        self.assertEquals(valid_words["hola"], 3)
        self.assertEquals(valid_words["noticias"], 1)

    def test_html_clean_stopwords_es(self):
        self.perform_html_visited(url= "http://molamazisimo.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>desde mi casa pienso cosas de casa </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        valid_words = collection.find()[0]["keywords_freq"]["text"]
        self.assertNotIn("desde", valid_words)
        self.assertNotIn("mi", valid_words)
        self.assertNotIn("de", valid_words)

    def test_html_clean_stopwords_en(self):
        self.perform_html_visited(url= "http://molamazisimo.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"last news\">"
                                             "</head><body><a>from my home i think about things of home </a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        valid_words = collection.find()[0]["keywords_freq"]["text"]
        self.assertNotIn("from", valid_words)
        self.assertNotIn("my", valid_words)
        self.assertNotIn("i", valid_words)
        self.assertNotIn("about", valid_words)
        self.assertNotIn("of", valid_words)

    def test_detect_language_spanish(self):
        self.perform_html_visited(url= "http://molamazisimo.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>esto es un texto en español claramente</a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        language = collection.find()[0]["language"]
        self.assertEquals(language, "spanish")

    def test_detect_language_english(self):
        self.perform_html_visited(url= "http://itiscoolalot.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"last news\">"
                                             "</head><body><a>this of course is an english text oh my god!</a></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        language = collection.find()[0]["language"]
        self.assertEquals(language, "english")

    def test_clean_html(self):
        self.perform_html_visited(url= "http://molamazisimo.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>esto es un html muy limpito</a>"
                                             "<div> lol</div><p> lolazooooo</p></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.htmlVisited
        clean_html = collection.find()[0]["clean_html"]
        self.assertEquals(clean_html, "esto es un html muy limpito lol lolazooooo")

    def test_process_keywords(self):
        self.perform_html_visited(url= "http://molamazisimo.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias de última\">"
                                             "</head><body><a>limpito</a>"
                                             "<div> lol</div><p> lolazo lolazo</p></html>",
                                  date="2014-01-01 00:00:00")
        collection = self.test_mongo.db.userKeywords
        collectionHtml = self.test_mongo.db.htmlVisited
        self.assertNotIn("processed", collectionHtml.find()[0])
        call_command('process_keywords')
        user_keywords = collection.find()[0]
        site_keywords = user_keywords["site_keywords_freq"]
        user = user_keywords["user"]
        metadata_keywords = user_keywords["metadata_keywords_freq"]
        self.assertEquals(site_keywords["lolazo"], 2)
        self.assertEquals(site_keywords["lol"], 1)
        self.assertEquals(site_keywords["limpito"], 1)
        self.assertEquals(metadata_keywords["noticias"], 1)
        self.assertEquals(metadata_keywords["última"], 1)
        self.assertEqual(collectionHtml.find()[0]["processed"], True)
        self.perform_html_visited(url= "http://molamazisimomas.com",
                                  html_code= "<hmtl><head><meta name=\"description\" content=\"Noticias\">"
                                             "</head><body><a>limpito limpito</a>"
                                             "<div> lol</div><p> lolazo lolazo</p></html>",
                                  date="2014-01-01 00:00:00")
        self.assertNotIn("processed", collectionHtml.find()[1])
        call_command('process_keywords')
        user_keywords = collection.find()[0]
        site_keywords = user_keywords["site_keywords_freq"]
        metadata_keywords = user_keywords["metadata_keywords_freq"]
        self.assertEquals(site_keywords["lolazo"], 4)
        self.assertEquals(site_keywords["lol"], 2)
        self.assertEquals(site_keywords["limpito"], 3)
        self.assertEquals(metadata_keywords["noticias"], 2)
        self.assertEquals(metadata_keywords["última"], 1)
        self.assertEqual(collectionHtml.find()[1]["processed"], True)
        self.assertEqual(user, "alfredo")


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

    def get_pages_visited(self, session_token=None):

        if session_token is None:
            session_token = self.session_token

        return self.api_client.get(API_URI['page_visited'], format='json',
                                   HTTP_SESSION_TOKEN=session_token)

    def get_page_categories(self, page_id, session_token=None):

        if session_token is None:
            session_token = self.session_token

        return self.api_client.get(API_URI['page_categories'] % page_id, format='json',
                                   HTTP_SESSION_TOKEN=session_token)


    ######################
    # Security tests
    ######################
    def test_invalid_session_token(self):
        resp = self.perform_page_visited(url="http://www.lol.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token + "a")
        self.assertHttpUnauthorized(resp)

    def test_no_user(self):
        other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
        other_user_resource = UserResource().get_resource_uri(other_user)

        resp = self.perform_page_visited(url="http://www.lol.com",
                                         user_resource=other_user_resource,
                                         session_token=self.session_token)
        self.assertHttpUnauthorized(resp)

    def test_post_to_other_user(self):
        other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
        other_user_resource = UserResource().get_resource_uri(other_user)

        resp = self.perform_page_visited(url="http://www.google.com",
                                         user_resource=other_user_resource,
                                         session_token=self.session_token)
        self.assertHttpUnauthorized(resp)

    def test_get_without_session(self):
        resp = self.get_pages_visited(session_token="")
        self.assertHttpUnauthorized(resp)

    def test_get_other_user_pages_visited(self):
        other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
        other_user_token = other_user.new_session(self.client)
        other_user_resource = UserResource().get_resource_uri(other_user)

        # Other user adds page visited
        resp = self.perform_page_visited(url="http://www.google.com",
                                         user_resource=other_user_resource,
                                         session_token=other_user_token)
        self.assertHttpCreated(resp)

        # Our user adds two pages
        resp = self.perform_page_visited(url="http://www.vivaejpania.com",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token)
        self.assertHttpCreated(resp)

        resp = self.perform_page_visited(url="http://www.manquepierda.net",
                                         user_resource=self.user_resource,
                                         session_token=self.session_token)
        self.assertHttpCreated(resp)

        resp = self.get_pages_visited()
        deserialized_resp = self.deserialize(resp)

        # We should see only our pages
        self.assertEqual(deserialized_resp["meta"]["total_count"], 2)

    def test_get_categories_without_sesion(self):
        self.perform_page_visited(url="http://www.vivaejpania.com")
        resp = self.get_page_categories(page_id=1, session_token="asdasd")
        self.assertHttpUnauthorized(resp)

    def test_get_categories_of_not_owned_page(self):
        other_user = User.objects.create_user("Kuntakinte", "kunta@gmail.com", "joasjoasjoas")
        other_user_token = other_user.new_session(self.client)
        other_user_resource = UserResource().get_resource_uri(other_user)

        # Other user adds page visited
        resp = self.perform_page_visited(url="http://www.google.com",
                                         user_resource=other_user_resource,
                                         session_token=other_user_token)
        self.assertHttpCreated(resp)

        # We try to access its categories
        inserted_page = PageVisited.objects.latest('id')
        resp = self.get_page_categories(page_id=inserted_page.id, session_token=self.session_token)
        self.assertHttpUnauthorized(resp)

    ######################
    # Parameters checks
    ######################

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

    def test_get_pages_visited(self):
        resp = self.perform_page_visited(url="http://www.one.com")
        self.assertHttpCreated(resp)

        resp = self.perform_page_visited(url="http://www.two.com")
        self.assertHttpCreated(resp)

        resp = self.perform_page_visited(url="http://www.three.com")
        self.assertHttpCreated(resp)

        resp = self.perform_page_visited(url="http://www.four.com")
        self.assertHttpCreated(resp)

        resp = self.get_pages_visited()
        deserialized_resp = self.deserialize(resp)

        self.assertEqual(deserialized_resp["meta"]["total_count"], 4)
        self.assertEqual(len(deserialized_resp["objects"]), 4)

    def test_get_pages_categories(self):
        resp = self.perform_page_visited(url="http://www.lol.com")
        self.assertHttpCreated(resp)

        inserted_page = PageVisited.objects.latest('id')
        resp = self.get_page_categories(inserted_page.id)
        self.assertHttpOK(resp)

        resp_data = self.deserialize(resp)
        self.assertEqual(resp_data, ['Humor'])

        resp = self.perform_page_visited(url="http://stackoverflow.com")
        self.assertHttpCreated(resp)

        inserted_page = PageVisited.objects.latest('id')
        resp = self.get_page_categories(inserted_page.id)
        self.assertHttpOK(resp)

        resp_data = self.deserialize(resp)
        self.assertEqual(set(resp_data),
                         set(['Software/Technology', 'Research/Reference', 'Forums/Message boards']))

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

    def test_get_other_user_search_query(self):
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

