from django.db import models
from django.contrib.auth.models import AbstractUser

from nltk import FreqDist

import models_mongo

# TODO: Documentar modelo

username_MAX_LENGTH = 40
PASSWORD_MAX_LENGTH = 100
URL_MAX_LENGTH = 500
SEARCH_QUERY_MAX_LENGTH = 300
CATEGORY_MAX_LENGTH = 50
TAXONOMY_MAX_LENGTH = 10


class UserCategory(models.Model):
    name = models.CharField(max_length=CATEGORY_MAX_LENGTH)
    taxonomy = models.CharField(max_length=TAXONOMY_MAX_LENGTH)

    class Meta:
        db_table = "user_category"

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





class UserCategorization(models.Model):
    user = models.ForeignKey(User)
    category = models.ForeignKey(UserCategory)
    weigh = models.IntegerField()

    class Meta:
        db_table = "user_categorization"

class PageVisited(models.Model):
    user = models.ForeignKey(User)
    page_visited = models.CharField(max_length=URL_MAX_LENGTH)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pages_visited"


class Search(models.Model):
    search_query = models.CharField(max_length=SEARCH_QUERY_MAX_LENGTH)
    search_results = models.CharField(max_length=URL_MAX_LENGTH)
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "searches"

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
