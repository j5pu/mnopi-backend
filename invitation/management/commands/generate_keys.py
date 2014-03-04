""""
This command generates new invitation keys
"""
from django.core.management.base import BaseCommand
import random
from string import ascii_letters, digits
from invitation.models import InvitationKey

class Command(BaseCommand):
    args = 'Num invitation keys'
    help = 'Generates a given number of invitation keys'

    def handle(self, *args, **options):

        num_keys = int(args[0])

        for i in range(0, num_keys):
            random_key = ''.join([random.choice(ascii_letters + digits) for x in range(30)])
            InvitationKey.objects.create(key=random_key, used=False)
            print "Created key: " + random_key