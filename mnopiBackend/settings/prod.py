"""Production settings and globals."""

from common import *

# Production secret
#########################################
#SECRET_KEY = os.environ['SECRET_KEY'] #TODO

# Production database
#########################################
DATABASES = {
    "default": {
    "ENGINE": "django.db.backends.mysql",
    "NAME": "mnopi",
    "USER": "root",
    "PASSWORD": "1aragon1",
    "HOST": "localhost",
    "PORT": "",
    }
}
##########################################

# DEBUG MODE IS OFF!!
####################################
DEBUG = False
TEMPLATE_DEBUG = DEBUG
####################################


# Only allowed hosts!!
####################################
ALLOWED_HOSTS = ['localhost:8000', '127.0.0.1', '.compute.amazonaws.com', '.compute-1.amazonaws.com']
####################################


# YahooId  : labelee_server@yahoo.com
# Password : 1Aragon1
ADMINS = (
    ('Labeloncio', 'labelee_server@yahoo.com'),
    ('Mnopi-server', 'mnopi.server@gmail.com'),
)

MANAGERS = ADMINS