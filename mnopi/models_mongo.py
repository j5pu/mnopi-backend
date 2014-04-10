from mnopimining import html, keywords, language


from HTMLParser import HTMLParser
import datetime
import nltk
from pymongo import MongoClient


db = MongoClient().mnopi # TODO: casque cuando no hay

def register_html_visited(page_visited, user, html_code):
    """
    Saves an htmlVisited object in the database

    Returns the _id ob the object created
    """

    html_visited = HtmlVisited(page_visited, html_code, user)
    html_visited.process()
    object_id = db.htmlVisited.insert(html_visited.__dict__)
    return object_id

def get_user_html_visited(user):
    """ Gets the complete html code history of an user """
    return list(db.htmlVisited.find({'user': user}))

def get_non_processed_keywords():
    """
    Retrieves list of keywords/frequency for every page not processed
    The page is then marked as processed.
    Returns a list of dictionaries of the form
              {'user': 'alfredo',
               'site_keywords_freq': {u'keyword_1': 2, u'keyword_2': 5 ...}
               'metadata_keywords_freq: {u'keyword_1': 2, u'keyword_2': 5 ...}}
    one for each html page
    """
    not_processed_pages = db.htmlVisited.find({'processed': {'$exists': False}})
    users_keywords = []
    for not_processed_page in not_processed_pages:
        users_keywords.append({'user': not_processed_page['user'],
                              'site_keywords_freq': not_processed_page['keywords_freq']['text'],
                              'metadata_keywords_freq': not_processed_page['keywords_freq']['metadata']})
        not_processed_page['processed'] = True
        db.htmlVisited.save(not_processed_page)

    return users_keywords

def get_user_keywords(username):
    """
    Retrieves the dictionary of keywords/frequency stored for an user
    """
    user_keywords = db.userKeywords.find_one({'user': username})
    if user_keywords == None:
        return {'user': username,
                'site_keywords_freq': {},
                'metadata_keywords_freq': {}}
    else:
        return user_keywords



def set_users_keywords(user_keywords_document):
    db.userKeywords.save(user_keywords_document)

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
        if date==None:
            self.date = datetime.datetime.utcnow()
        else:
            self.date = date

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

        # Even in unicode, there could be html entities like &aocute
        parser = HTMLParser()
        unescaped_text = parser.unescape(self.html_code)

        self.clean_html = nltk.clean_html(unescaped_text)

    def _process_properties(self):
        """Computes site properties from html metadata"""
        parser = HTMLParser()
        unescaped_text = parser.unescape(self.html_code)

        self.properties = html.get_html_metadata(unescaped_text)

    def _detect_language(self):
        """Detects the language of the page"""
        self.language = language.detect_language(self.clean_html)

    def _process_keywords_freq(self):
        """Gets distribution of keywords frequency"""
        self.keywords_freq = {
            'text': keywords.get_freq_words(self.clean_html, self.language),
            'metadata': keywords.get_freq_words(" ".join(self.properties.values()), self.language)
        }
