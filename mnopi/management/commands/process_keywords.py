"""
This command processes website and metadata keywords which are stored in
MongoDB's htmlVisited tables. The keywords are added to the user profiles,
which are recorded in keywords SQL tables, so they are easily accessed when
needed
"""
import mnopi.models_mongo as models_mongo


from django.core.management.base import BaseCommand

class Command(BaseCommand):
    args = ''
    help = 'Adds not processed keywords from html pages into user profiles'

    def handle(self, *args, **options):

        def add_frequencies(from_dict, to_dict):
            for keyword in from_dict:
                if keyword in to_dict:
                    to_dict[keyword] += from_dict[keyword]
                else:
                    to_dict[keyword] = from_dict[keyword]

        users_keywords = models_mongo.get_non_processed_keywords()
        # Each page reports a set of metadata and site keywords for the user who visited it
        i = 0
        for user_keywords in users_keywords:
            print i
            i += 1
            current_user_keywords = models_mongo.get_user_keywords(user_keywords['user'])
            add_frequencies(from_dict=user_keywords['site_keywords_freq'],
                            to_dict=current_user_keywords['site_keywords_freq'])
            add_frequencies(from_dict=user_keywords['metadata_keywords_freq'],
                            to_dict=current_user_keywords['metadata_keywords_freq'])
            models_mongo.set_users_keywords(current_user_keywords)