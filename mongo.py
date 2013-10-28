from pymongo import MongoClient
import datetime
import logging

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


def update_user(user_key, categories):
    """
    Updates the number of visits to categories for a given user, using the last page visited
    """

    db = mongo.mnopi
    user = db.users.find_one({'email' : user_key})
    for cat in categories:
        add_visit_to_category(user, cat)
    db.users.save(user)

def add_visit_to_category(user, category):

    if category not in user.keys():
        user[category] = 1
    else:
        user[category] += 1

def mongo_init():
    """
    Initialization of MongoDB instance.
    """
    try:
        mongo = MongoClient()
    except:
        raise MongoNotLoadedException





