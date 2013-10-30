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

def serve_html_visited(url, user_key, html_code):
    """
    Registers the html code of an url visited by the user
    """

    mongo.register_html(url, user_key, html_code)

def serve_search_done(search_query, search_results, user_key):
    """
    Registers search queries performed by users
    """

    mongo.register_search(search_query, search_results, user_key)
