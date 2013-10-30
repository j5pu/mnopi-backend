import urlparse
import urllib
import re

import mongo
import opendns

RELEVANT_META_PROPERTIES = ["keywords",
                            "description"]

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

    html_code = urllib.unquote(html_code.replace("\t", "").replace("\n", ""))
    relevant_properties = process_html_page(html_code)
    mongo.register_html(url, user_key, html_code, relevant_properties)

def serve_search_done(search_query, search_results, user_key):
    """
    Registers search queries performed by users
    """

    mongo.register_search(search_query, search_results, user_key)

def process_html_page(html_code):
    """
    Process html code and gets relevant properties
    """
    properties_list = []

    # Retrieve important meta properties
    meta_tags = re.findall("<meta.*/>", html_code)
    for tag in meta_tags:
        relevant_tag = match_relevant_meta(tag)
        if relevant_tag:
            properties_list.append(relevant_tag)

    # Title of page
    title_match = re.search("<title>(.*)</title>", html_code)
    if title_match:
        title = title_match.groups()[0]
        properties_list.append(("title", title))

    return properties_list

def match_relevant_meta(meta_tag):
    """
    Return tuples (name, content) of relevant meta properties
    <meta name="description" content="Fancy webpage" -> ("description", "Fancy webpage")
    """
    for tag in RELEVANT_META_PROPERTIES:
        name_matcher = re.compile("name.*?\"(.*?)\"")
        match = name_matcher.search(meta_tag)
        if match:
            meta_name = match.groups()[0]

            # Check if the type of meta data is of our interest
            if meta_name == tag:
                content_matcher = re.compile("content.*?\"(.*?)\"")
                match = content_matcher.search(meta_tag)
                meta_content = match.groups()[0]

                return (meta_name, meta_content)

    return None
