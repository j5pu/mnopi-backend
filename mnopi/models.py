from django.db import models

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import connection
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import utc

from nltk import FreqDist

import datetime
import os
import base64

import models_mongo
import constants

# TODO: Documentar modelo
# Ojo, hay una redundandia en el modelo entre las categorias de las paginas visitadas y el peso de cada
# categoria con el usuario. Esto esta hecho aposta por temas de rendimiento

PASSWORD_MAX_LENGTH = 100
URL_MAX_LENGTH = 500
SEARCH_QUERY_MAX_LENGTH = 300
CATEGORY_MAX_LENGTH = 50
TAXONOMY_MAX_LENGTH = 10
KEYWORD_MAX_LENGTH = 50
CLIENT_MAX_LENGTH = 50
MONGO_DB_ID_LENGTH = 24

METADATA_KEYWORD = 1
SITE_KEYWORD = 2

class UserCategory(models.Model):
    name = models.CharField(max_length=CATEGORY_MAX_LENGTH)
    taxonomy = models.CharField(max_length=TAXONOMY_MAX_LENGTH)

    class Meta:
        db_table = "user_categories"

class User(AbstractUser):
    """
    Extends Django basic authorization user
    """
    categories = models.ManyToManyField(UserCategory, through='UserCategorization')

    class Meta:
        db_table = "users"

    def get_keywords_freqs_from_html(self, keywords_limit=None):
        """
        Computes keywords frequency from the users list of precomputed keywords from html
        DEPRECATED: use get_site_keywords
        TODO: Refactor for testing purposes
        """
        keywords = models_mongo.get_user_html_keywords_freqs(user=self.username)
        word_freqs = FreqDist()
        for page_keywords in keywords:
            word_freqs += page_keywords['text']

        if not keywords_limit:
            return zip(word_freqs.keys(), word_freqs.values())
        else:
            return zip(word_freqs.keys()[:keywords_limit],
                       word_freqs.values()[:keywords_limit])

    def get_keywords_freqs_from_properties(self, keywords_limit=None):
        """
        Computes keywords for a user using meta data in the visited pages
        DEPRECATED: use get_keywords
        TODO: Refactor for testing purposes
        """
        keywords = models_mongo.get_user_html_keywords_freqs(user=self.username)
        word_freqs = FreqDist()
        for page_keywords in keywords:
            word_freqs += page_keywords['metadata']

        if not keywords_limit:
            return zip(word_freqs.keys(), word_freqs.values())
        else:
            return zip(word_freqs.keys()[:keywords_limit],
                       word_freqs.values()[:keywords_limit])

    def get_keywords_hash(self, type):
        """
        Gets the precomputed dict of keywords for an user and their associated frequencies
        Type can be METADATA_KEYWORDS or SITE_KEYWORDS
        """
        if type == SITE_KEYWORD:
            keywords_freq = models_mongo.get_user_keywords(self.username)['site_keywords_freq']
        else:
            keywords_freq = models_mongo.get_user_keywords(self.username)['metadata_keywords_freq']

        return keywords_freq

    def get_ordered_keywords_list(self, type, keywords_limit=None):
        """
        Order the precomputed list of keywords for an user and returns keywords frequency
        Type can be METADATA_KEYWORDS or SITE_KEYWORDS
        """
        keywords_freq = self.get_keywords_hash(type)

        keywords_freq_list = zip(keywords_freq.keys(), keywords_freq.values())
        keywords_freq_list.sort(cmp=lambda x, y: cmp(x[1], y[1]), reverse=True)
        return keywords_freq_list[:keywords_limit]

    def get_domains_by_category(self):
        """
        Computes a list of categories and the sites visited by the user for each one
        Works only on OpenDns categorized domains
        Returns a dict with domains listed by category:
             {"News/Media": ["elpais.com", "www.elmundo.es", ...],
              "CategoryX" : ["blabla.com", ...] }
        """
        sql = ('SELECT DISTINCT domain, user_categories.name as category '
               'FROM users INNER JOIN pages_visited ON (users.id = pages_visited.user_id) '
                          'INNER JOIN domains ON (pages_visited.domain_id = domains.id) '
                          'INNER JOIN domains_categories ON (domains.id = domains_categories.categorizeddomain_id) '
                          'INNER JOIN user_categories ON (domains_categories.usercategory_id = user_categories.id) '
               'WHERE username = %s')

        # Username automatically escaped
        cursor = connection.cursor()
        cursor.execute(sql, [self.username])

        categorized_domains = {}
        for (domain, category) in cursor.fetchall():
            if category in categorized_domains:
                categorized_domains[category].append(domain)
            else:
                categorized_domains[category] = [domain]

        return categorized_domains

    def get_visits_by_category(self):
        """
        Gets a dict of categories and number of visits to each category by an user
        Uses database redundancy data, it is faster than getting the same information with
        the method get_domains_by_category

        Returns [('category' : "CategoryX", 'visits' : 5),
                 ('category' : "CategoryY", 'visits' : 23) ...]
        """
        categories = self.categories.all()
        visits_by_category = [UserCategorization.objects.get(user=self, category=cat).weigh for cat in categories]
        visits_by_category_list = [{'category': x.name, 'visits': y} for (x, y) in zip(categories, visits_by_category)]
        return visits_by_category_list

    def update_categories_visited(self, categories):
        """
        Updates the number of visits to categories for a given user
        """
        database_categories = [UserCategory.objects.get(name=cat) for cat in categories]
        for cat in database_categories:
            categorization, created = \
                UserCategorization.objects.get_or_create(user=self, category=cat,
                                                         defaults={'weigh': 0})
            categorization.weigh += 1
            categorization.save()

    def get_searches_done(self,
                          datetime_from=datetime.datetime.min,
                          datetime_to=None):
        """
        Get searches queries done in a time interval by the user
        """
        if datetime_to is None:
            datetime_to = datetime.datetime.utcnow().replace(tzinfo=utc)

        return Search.objects.filter(user=self, date__gte=datetime_from, date__lte=datetime_to)

    def new_session(self, client):
        """
        Opens a new session for the user in the specified client
        """
        session_token = base64.b64encode(os.urandom(32))
        ClientSession.objects.create(user=self, session_token=session_token, client=client)

        return session_token

class CategorizedDomain(models.Model):
    domain = models.CharField(max_length=URL_MAX_LENGTH)
    categories = models.ManyToManyField(UserCategory)

    class Meta:
        db_table = "domains"

    def add_categories(self, categories):
        """
        Adds categories to a domain.
        For instance: add [News/Media, Technology] to 'www.cnn.com'
        """
        database_categories = [UserCategory.objects.get(name=cat) for cat in categories]
        for cat in database_categories:
            self.categories.add(cat)

class UserCategorization(models.Model):
    user = models.ForeignKey(User)
    category = models.ForeignKey(UserCategory)
    weigh = models.IntegerField()

    class Meta:
        db_table = "user_categorization"


class Client(models.Model):
    """
    Clients that can get connected to the system, such as android applications or browser plugins
    """
    client_name = models.CharField(max_length=CLIENT_MAX_LENGTH)
    allowed = models.BooleanField(default=True)

    #class Meta:
        #db_table = "clients" # TODO: Change name for consistency

class PageVisited(models.Model):
    user = models.ForeignKey(User)
    page_visited = models.CharField(max_length=URL_MAX_LENGTH)
    domain = models.ForeignKey(CategorizedDomain)
    date = models.DateTimeField(auto_now_add=False)
    client = models.ForeignKey(Client)
    html_ref = models.CharField(max_length=MONGO_DB_ID_LENGTH, )

    class Meta:
        db_table = "pages_visited"


class Search(models.Model):
    search_query = models.CharField(max_length=SEARCH_QUERY_MAX_LENGTH)
    search_results = models.CharField(max_length=URL_MAX_LENGTH)
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=False)
    client = models.ForeignKey(Client)

    class Meta:
        db_table = "searches"

def get_new_expiration_time(): # TODO : mover a un utils.py?
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    return now + datetime.timedelta(days=constants.PLUGIN_SESSION_EXPIRY_DAYS)

class ClientSession(models.Model):

    user = models.ForeignKey(User)
    expiration_time = models.DateTimeField(default=get_new_expiration_time)
    session_token = models.CharField(max_length=128)
    client = models.ForeignKey(Client)

    # Note: At the moment, no checks are done that renew logins are made by the same client

    class Meta:
        db_table = "client_sessions"