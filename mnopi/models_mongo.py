from mnopimining import html, keywords, language

import datetime
import nltk
from pymongo import MongoClient

db = MongoClient().mnopi # TODO: casque cuando no hay

def register_html_visited(page_visited, user, html_code):
    """ Saves an htmlVisited object in the database """

    html_visited = HtmlVisited(page_visited, html_code, user)
    html_visited.process()
    db.htmlVisited.insert(html_visited.__dict__)

def get_user_html_visited(user):
    """ Gets the complete html code history of an user """
    return list(db.htmlVisited.find({'user': user}))

def get_user_html_keywords_freqs(user):
    """ Retrieves list of keywords/frequency for each html saved in the database """
    keywords_list = list(db.htmlVisited.find({'user': user}, {'_id': 0, 'keywords_freq': 1}))
    keywords_list = [x['keywords_freq'] for x in keywords_list]
    return keywords_list

class HtmlVisited(object):
    """
    Model for html saved pages
    They are saved in a MongoDB instance different to the main database, in SQL
    This class encapsulates all actions with the htmlVisited rows of the mongoDB
    """

    def __init__(self, page_visited, html_code, user, date=None):
        """
        Upon creation, if no date is specified, it will be automatically added
        """
        self.page_visited = page_visited
        self.html_code = html_code
        self.user = user
        self.date = datetime.datetime.utcnow()

    def process(self):
        """
        Process html code and retrieves important features for data analysis
        """
        self._clean_html_text()
        self._process_properties()
        self._detect_language()
        self._process_keywords_freq()

    def _clean_html_text(self):
        """Computes the site clear text without html code"""
        self.clean_html = nltk.clean_html(self.html_code)

    def _process_properties(self):
        """Computes site properties from html metadata"""
        self.properties = html.get_html_metadata(self.html_code)

    def _detect_language(self):
        """Detects the language of the page"""
        self.language = language.detect_language(self.clean_html)

    def _process_keywords_freq(self):
        """Gets distribution of keywords frequency"""
        self.keywords_freq = {
            'text': keywords.get_freq_words(self.clean_html, self.language),
            'metadata': keywords.get_freq_words(" ".join(self.properties.values()), self.language)
        }




