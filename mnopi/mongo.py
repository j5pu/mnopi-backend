"""
Mongo.py . Model layer for mongo.py
WARNING: This module is deprecated
"""
from pymongo import MongoClient
import datetime
import logging

from hashlib import sha256 # TODO: Check better security options

class MongoNotLoadedException(Exception):
    pass

# Mongo instance
mongo = MongoClient()

def register_visit(page_visited, user):
    """
    Register page in the collection of pages visited
    """

    db = mongo.mnopi
    page_visited = {"pageVisited" : page_visited,
                    "user" : user,
                    "date" : datetime.datetime.utcnow()}
    db.pagesVisited.insert(page_visited) # TODO Anyadir control de errores o algo??

def register_html(page_visited, user, html_code, relevant_properties=[], keywords_freq=[]):
    """
    Saves html code in database for a visited page
    """

    db = mongo.mnopi

    html_visited = {"pageVisited" : page_visited,
                    "user" : user,
                    "date" : datetime.datetime.utcnow(),
                    "htmlCode" : html_code,
                    "keywordsFreq" : keywords_freq}

    # Add special retrieved properties, such as meta data or title
    if relevant_properties:
        html_visited['properties'] = {}
        for (property, value) in relevant_properties:
            html_visited['properties'][property] = value

    db.htmlVisited.insert(html_visited)

def register_search(search_query, search_results, user):
    """
    Saves search query and results in database
    """

    db = mongo.mnopi
    search = {"searchQuery" : search_query,
              "searchResults" : search_results,
              "user" : user,
              "date" : datetime.datetime.utcnow()}

    db.searches.insert(search)

def set_domain_saved_categories(domain, categories):
    """
    Saves categories for a domain to avoid new queries to OpenDNS.com
    """

    db = mongo.opendns
    domain_categories = {"domain" : domain,
                         "categories" : categories}

    db.domains.insert(domain_categories)

def get_domain_saved_categories(domain):
    """
    Gets categories previously retrieved in OpenDns connections

    Returns the list of categories or None if the domain was not previously saved
    """

    db = mongo.opendns
    domain = db.domains.find_one( {"domain" : domain})
    if domain:
        return domain['categories']
    else:
        return None

def user_exists(user_key):
    """
    Checks if a given user exists in the database
    """

    db = mongo.mnopi
    user = db.users.find_one({'user_key' : user_key})
    if user:
        return True
    return False

def authenticate_user(user_key, password):
    """
    Authenticates user with password
    """

    db = mongo.mnopi
    user = db.users.find_one({'user_key' : user_key})
    hashed_password = sha256(password).hexdigest()

    return hashed_password == user['password']

def add_user(user_key, password):
    """
    Adds a new user to the database. It doesn't check previous existence
    """

    hashed_password = sha256(password).hexdigest()

    db = mongo.mnopi
    new_user = {"user_key" : user_key,
                "password" : hashed_password,
                "categories" : {}}
    db.users.save(new_user)

def update_user(user_key, categories):
    """
    Updates the number of visits to categories for a given user, using the last page visited
    """

    db = mongo.mnopi
    user = db.users.find_one({'user_key' : user_key})
    for cat in categories:
        add_visit_to_category(user, cat)
    db.users.save(user)

def get_urls_visited(user_key):
    """
    Gets a list of all urls visited by an user. It doesn't check user existence.
    Returns ( {'pageVisited' :  "www.blahblah.com", 'date' : datetime}, { ... } ... )
    """
    #TODO: esto devolver listas super tochas en el futuro, ojo!

    db = mongo.mnopi
    urls_visited =  list(db.pagesVisited.find({'user' : user_key},
                                             {'_id' : 0, 'pageVisited' : 1, 'date' : 1}))
    return urls_visited

def get_searches_done (user_key):
    """
    Gets a list of searches done by an user. It doesn't check user existence.
    Returns ( {'searchQuery' : 'blabla', 'date': datetime}, {...}, ... )
    """

    db = mongo.mnopi
    searches_done = list(db.searches.find({'user' : user_key},
                                             {'_id' : 0, 'searchQuery' : 1, 'date' : 1}))
    return searches_done


def add_visit_to_category(user, category):

    if category not in user['categories'].keys():
        user['categories'][category] = 1
    else:
        user['categories'][category] += 1

def mongo_init():
    """
    Initialization of MongoDB instance.
    """
    try:
        mongo = MongoClient()
    except:
        raise MongoNotLoadedException

def retrieve_user_html_visited(user):
    """
    Retrieves all html pages visited by an user
    """
    #TODO: Alerta, esto puede volverse hiper mega tocho

    db = mongo.mnopi
    html_visited = list(db.htmlVisited.find({'user' : user}))
    return html_visited

def retrieve_user_html_keywords_freqs(user):
    """
    Retrieves list of keywords/frequency for each html saved in the database
    """

    db = mongo.mnopi
    keywords_list = list(db.htmlVisited.find({'user' : user}, {'_id': 0, 'keywordsFreq': 1}))
    keywords_list = [x['keywordsFreq'] for x in keywords_list]
    return keywords_list

def get_user_categories(user):
    """
    Gets a list of categories and number of pages visited in that category
    for a user
    """
    db = mongo.mnopi
    categories = db.users.find_one({'user_key': user}, {'_id': 0, 'categories': 1})
    return categories['categories']