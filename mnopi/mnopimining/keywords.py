# -*- coding: utf-8 -*-
from nltk.tokenize import word_tokenize

from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk import FreqDist

import string

REMOVE_PUNCTUATION_MAPPING = dict.fromkeys(map(ord, string.punctuation))
SPANISH_STOPWORDS_UNICODE = [unicode(word, 'utf-8') for word in stopwords.words('spanish')]

def remove_punctuation(tokens):
    """
    Removes punctuation from a list of tokens
    It uses string.punctuation list of punctuation
    """
    no_punct_words = []
    for token in tokens:

        # Some unicode punctuation characters will be lost! Review
        # http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
        # for other options.
        no_punct_token = token.translate(REMOVE_PUNCTUATION_MAPPING)
        if not no_punct_token == '':
            no_punct_words.append(no_punct_token)

    return no_punct_words

def clean_stopwords(words, language='english'):
    """
    Removes stopwords from a list of words
    """
    no_stop_words = []
    for word in words:
        # TODO: review esto, de momento se queda que ni español ni english es aceptado, habria que quitar english siempre
        # y tambien quitar el idioma nativo, por ejjmplo a mi me sale quie twitter es ingles y no me quita las stop de
        # espanyol
        # OTRA OPCION ES QUITAR DIRECTAMENTE TODAS
        # TODO: falta tambien por ver quitar las palabras comunes sin tildes (mal escritas)
        # never include English stopwords, as it is ubiquitous in the web
        # if (not word in stopwords.words(language) and
        #         (language == 'english' or\
        #         not word in stopwords.words('english'))):
        #     no_stop_words.append(word)
        if (not word in stopwords.words('english') and
        not word in SPANISH_STOPWORDS_UNICODE):
            no_stop_words.append(word)

    return no_stop_words

def clean_invalid_words(words):
    """
    Removes some special tokens that are not worthy to save
    """
    valid_words = []
    for word in words:
        if not word.isdigit() and not len(word) == 1:
            valid_words.append(word)

    return valid_words

def stem_words(words, language='english'):
    """
    Stems words in a list of words
    """
    stemmer = SnowballStemmer(language)
    stemmed_words = []
    for word in words:
        stemmed_words.append(stemmer.stem(word))

    return stemmed_words

def get_words(text, stem=False, language='english'):
    """
    Given a text, it returns a list of stemmed and cleaned words
    Steps: - Tokenize words
           - Remove punctuation
           - Clean stopwords
           - (if stem = True) Stem words using stemmer
    """

    tokenized_words = word_tokenize(text)
    lower_tokenized_words = [token.lower() for token in tokenized_words]
    no_punct_words = remove_punctuation(lower_tokenized_words)
    no_stop_words = clean_stopwords(no_punct_words, language)
    valid_words = clean_invalid_words(no_stop_words)
    if stem:
        stemmed_words = stem_words(no_stop_words, language)
        return stemmed_words
    else:
        return no_stop_words

def get_freq_words(text, language='english'):
    """
    Given a text, it a FreqDist of processed words
    """
    words = get_words(text, stem=False, language=language)
    return FreqDist(words)

