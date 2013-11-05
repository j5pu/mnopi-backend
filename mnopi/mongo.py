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

def register_html(page_visited, user, html_code, relevant_properties=[]):
    """
    Saves html code in database for a visited page
    """

    db = mongo.mnopi

    html_visited = {"pageVisited" : page_visited,
                    "user" : user,
                    "date" : datetime.datetime.utcnow(),
                    "htmlCode" : html_code}

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