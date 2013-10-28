import urlparse

import mongo
import opendns

def serve_page_visited(url, user_key):
    """
    Registers an url visited by the user, updating data for its corresponding categories
    """

    url_domain = urlparse.urlparse(url)[1]
    categories = opendns.getCategories(url_domain)

    mongo.register_visit(url, user_key)
    mongo.update_user(user_key, categories)

    print "URL visitada: " + url
    print "Usuario: " + user_key
    print "Categories: " + str(categories)