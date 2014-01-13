"""
Intention Engine
Calculates intention by means of user data.
"""
from django.shortcuts import get_object_or_404
from django.utils.timezone import utc

from mnopi.models import User
import keywords

import datetime
import math


RELEVANT_INTENTION_DAYS = 40

def group_relevant_searches(relevant_searches):
    """
    Groups relevant searches by the use of the same object words, including the different dates
    For instance, all searches which denoted interest by the object "television" will be grouped together
    """
    search_groups = {}
    for relevant_search in relevant_searches:
        object_words = frozenset(relevant_search['object_words'])
        if object_words not in search_groups:
            search_groups[object_words] = {'dates': [relevant_search['date']],
                                          'intention_indexes': [relevant_search['intention_index']]}
        else:
            search_groups[object_words]['dates'].append(relevant_search['date'])
            search_groups[object_words]['intention_indexes'].append(relevant_search['intention_index'])

    # From present to past
    for group in search_groups:
        search_groups[group]['dates'].reverse()
        search_groups[group]['intention_indexes'].reverse()
    return search_groups

def get_smart_index(interest_group):
    """
    Gets the mnopi smart index for an interest search
    The smart index is the combination of two indexes, the immediate interest index, which measures
    interest close in time, and the continuous interest index, which adds more importance
    to intentions continuous in the time in contrast to those that are just recent.

    It returns the indices in the form
              (smart_index, immediate_int_index, continuous_int_index)
    """

    # List of days in the past in which the search for the object was done, from present to past
    days_list = []
    for date in interest_group['dates']:
        days_list.append((datetime.datetime.utcnow().replace(tzinfo=utc) - date).days)

    # Immediate interest index
    ii_index = 0.0
    for i in range(0, len(days_list)):
        ii_index += 1.0/(days_list[i]+1) * interest_group['intention_indexes'][i]
    ii_index = 2.0/math.pi * math.atan(ii_index) # Normalize to 1

    # Continuous interest index
    ci_brute = 0.0
    for i in range(0, len(days_list)):
        for j in range(i+1, len(days_list)):
            average_index = (interest_group['intention_indexes'][i] + interest_group['intention_indexes'][j])/2.0
            ci_brute += (days_list[j] - days_list[i]) * average_index
    ci_brute /= RELEVANT_INTENTION_DAYS
    ci_index = 2.0/math.pi * math.atan(ci_brute)

    # Smart index
    smart_index = (ci_index + ii_index)/2

    return smart_index, ii_index, ci_index

def compute_search_intentions(username, intention_keywords_set):
    """
    Computes intentions based on a set of relevant keywords that are
    looked upon the user search queries.

    Each intention is given a index value according to repeated searches
    in time, if any.
    """

    user = get_object_or_404(User, username=username)

    relevant_origin_date = datetime.datetime.utcnow().replace(tzinfo=utc) -\
                           datetime.timedelta(days=RELEVANT_INTENTION_DAYS)

    searches = user.get_searches_done(datetime_from=relevant_origin_date)

    relevant_searches = []
    for search in searches:
        search_words = keywords.get_words(search.search_query, stem=True, language='spanish') #TODO: adaptar a otros idiomas
        for i in range(0, len(search_words)):
            if search_words[i] in intention_keywords_set:
                # The search is relevant and words are distributed by whether they transmit intention
                # ("buy", "sell") or provide additional information about the intention ("television", "games")
                # The intention index is considered for all the words and added
                intention_words = [search_words[i]]
                intention_index = intention_keywords_set[search_words[i]]
                object_words = []
                for j in range (0, i):
                    object_words.append(search_words[j])
                for j in range(i+1, len(search_words)):
                    if search_words[j] in intention_keywords_set:
                        intention_words.append(search_words[j])
                        intention_index += intention_keywords_set[search_words[j]]
                    else:
                        object_words.append(search_words[j])

                relevant_search = {}
                relevant_search['intention_words'] = intention_words
                relevant_search['intention_index'] = intention_index if intention_index <= 1 else 1
                relevant_search['object_words'] = object_words
                relevant_search['query'] = search.search_query
                relevant_search['date'] = search.date
                relevant_searches.append(relevant_search)

                break

    interest_groups = group_relevant_searches(relevant_searches)
    for group in interest_groups:
        (smart_index, ii_index, ci_index) = get_smart_index(interest_groups[group])
        interest_groups[group]['smart_index'] = smart_index
        interest_groups[group]['ii_index'] = ii_index
        interest_groups[group]['ci_index'] = ci_index

    return interest_groups