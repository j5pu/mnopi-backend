import nltk
from nltk import FreqDist

import mnopi.mongo
import language
import keywords

def get_user_keywords_from_html_brute(user_key):
    """
    Computes keywords for a user using all html that he visited
    NOTE: This function implies heavy computation. Keywords have been
    already processed in database for each html present there
    """

    html_pages = mnopi.mongo.retrieve_user_html_visited(user_key)
    word_freqs = FreqDist()
    for page in html_pages:
        page_text = nltk.clean_html(page['htmlCode'])
        lang = language.detect_language(page_text)
        print page['pageVisited']
        print "idioma: " + lang
        words = keywords.get_words(page_text, stem=False, language=lang)
        word_freqs += words

    return word_freqs

def get_user_keywords_from_html(user_key, keywords_limit=None):
    """
    Computes keywords frequency from the users list of precomputed keywords for html
    DEPRECATED : moved to User model
    """

    keywords_list = mnopi.mongo.retrieve_user_html_keywords_freqs(user_key)
    word_freqs = FreqDist()
    for words in keywords_list:
        word_freqs += words['text']

    if not keywords_limit:
        return zip(word_freqs.keys(), word_freqs.values())
    else:
        return zip(word_freqs.keys()[:keywords_limit],
                   word_freqs.values()[:keywords_limit])

def get_user_keywords_from_properties(user_key):
    """
    Computes keywords for a user using meta data in the visited pages
    DEPRECATED: moved to User model
    """

    html_pages = mnopi.mongo.retrieve_user_html_visited(user_key) #todo: ojo super ineficiente, coger solo properties
    word_freqs = FreqDist()
    for page in html_pages:
        if 'properties' in page:
            text = " ".join(page['properties'].values())
            lang = language.detect_language(text)
            words = keywords.get_words(text, stem=False, language=lang)
            word_freqs += words

    return word_freqs #todo: refactor con metodo anterior
