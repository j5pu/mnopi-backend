# coding=utf-8
"""
Application customizable constants
"""

USER_KEYWORDS_NUMBER = 50

#
# Dashboard constants
#
DASHBOARD_MAIN_USER_KEYWORDS_NUMBER = 30
DASHBOARD_MAIN_METADATA_KEYWORDS_NUMBER = 30
DASHBOARD_MAIN_SEARCHES_NUMBER = 4
DASHBOARD_MAIN_PAGES_VISITED_NUMBER = 12

#
# User information lists constants
#
USER_PAGES_VISITED_PER_PAGE = 25
USER_SEARCHES_PER_PAGE = 25

USER_KEYWORDS_LIST_TOTAL = 200
USER_KEYWORDS_PER_PAGE = 25

USER_METADATA_KEYWORDS_LIST_TOTAL = 200
USER_METADATA_KEYWORDS_PER_PAGE = 25

#
# User registration constants
#
PASS_MIN_LENGTH = 6
PASS_MAX_LENGTH = 40

USERNAME_MIN_LENGTH = 1
USERNAME_MAX_LENGTH = 20

EMAIL_MAX_LENGTH = 80

REGISTRATION_FIELDS_ERROR = "Rellena todos los campos del formulario"
REGISTRATION_USER_EXISTS = "El usuario ya existe"
REGISTRATION_USER_EMPTY = "Introduce un identificador de usuario"
REGISTRATION_PASSWORDS_DONT_MATCH = "Las contraseñas no coinciden"
REGISTRATION_PASSWORD_ERROR = "La contraseña tiene que tener al menos " + str(PASS_MIN_LENGTH) + " caracteres"
REGISTRATION_CONDITIONS_ERROR = "Debes leer y aceptar las condiciones de uso"

#
# User login constants
#
LOGIN_FIELDS_ERROR = "Introduce datos de login"
LOGIN_USER_DOESNT_EXIST = "El usuario no existe"
LOGIN_BAD_PASSWORD = "Contraseña incorrecta"

#
# Plugin related values
#
PLUGIN_SESSION_EXPIRY_DAYS = 30