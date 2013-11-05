# coding=utf-8

from django.shortcuts import render
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import urlparse
import json
import re
import urllib

import mongo
import opendns

PASS_MIN_LENGTH = 6

REGISTRATION_FIELDS_ERROR = "Rellena todos los campos del formulario"
REGISTRATION_USER_EXISTS = "El usuario ya existe"
REGISTRATION_USER_EMPTY = "Introduce un identificador de usuario"
REGISTRATION_PASSWORDS_DONT_MATCH = "Las contraseñas no coinciden"
REGISTRATION_PASSWORD_ERROR = "La contraseña tiene que tener al menos " + str(PASS_MIN_LENGTH) + " caracteres"
REGISTRATION_CONDITIONS_ERROR = "Debes leer y aceptar las condiciones de uso"

LOGIN_FIELDS_ERROR = "Introduce datos de login"
LOGIN_USER_DOESNT_EXIST = "El usuario no existe"
LOGIN_BAD_PASSWORD = "Contraseña incorrecta"

RELEVANT_META_PROPERTIES = ["keywords",
                            "description"]


#TODO: Volver a poner y tratar el tema de csrf

def index(request):
    return render(request, 'mnopi/index.html')

def login(request):
    #TODO: cambiar utilizando el sistema de Django
    #TODO: incorporar checkeos javascript en interfaces

    def login_failed(message):
        return render(request, 'mnopi/index.html', {'error_message' : message})

    try:
        user_key = request.POST['user_key']
        password = request.POST['password']
    except(KeyError):
        return login_failed(LOGIN_FIELDS_ERROR)

    if user_key == "" or password == "":
        return login_failed(LOGIN_FIELDS_ERROR)
    elif not mongo.user_exists(user_key):
        return login_failed(LOGIN_USER_DOESNT_EXIST)
    elif not mongo.authenticate_user(user_key, password):
        return login_failed(LOGIN_BAD_PASSWORD)

    return render(request, 'mnopi/main.html')


def register(request):
    return render(request, 'mnopi/register.html')

def conditions(request):
    return render(request, 'mnopi/conditions.html')

def new_user(request):
    """
    Sign ups user to the system. It checks every parameter
    """

    def registration_failed(message):
        return render(request, 'mnopi/register.html', {'error_message' : message})

    try:
        user_key = request.POST['user_key']
        password = request.POST['password']
        password_repeat = request.POST['confirm']
    except(KeyError):
        return registration_failed(REGISTRATION_FIELDS_ERROR)

    if user_key == "":
        return registration_failed(REGISTRATION_USER_EMPTY)
    elif password != password_repeat:
        return registration_failed(REGISTRATION_PASSWORDS_DONT_MATCH)
    elif len(password) < PASS_MIN_LENGTH:
        return registration_failed(REGISTRATION_PASSWORD_ERROR)
    elif not request.POST.get('acceptance', False):
        return registration_failed(REGISTRATION_CONDITIONS_ERROR)
    elif mongo.user_exists(user_key):
        return render(request, 'mnopi/register.html', {'error_message' : REGISTRATION_USER_EXISTS})

    mongo.add_user(user_key, password)

    return render(request, 'mnopi/register_successful.html')

@csrf_exempt
def page_visited(request):
    """
    Registers an url visited by the user, updating data for its corresponding categories
    """

    post_data = json.loads(request.body)
    url = post_data['url']
    user_key = post_data['idUser']

    url_domain = urlparse.urlparse(url)[1]
    categories = opendns.getCategories(url_domain)

    mongo.register_visit(url, user_key)
    mongo.update_user(user_key, categories)

    return HttpResponse()

@csrf_exempt
def search_done(request):
    """
    Registers search queries performed by users
    """
    post_data = json.loads(request.body)
    search_results = post_data['searchResults']
    search_query = post_data['searchDone']
    user_key = post_data['idUser']

    mongo.register_search(search_query, search_results, user_key)

    return HttpResponse()

@csrf_exempt
def html_visited(request):
    """
    Registers the html code of an url visited by the user
    """

    post_data = json.loads(request.body)
    url = post_data['url']
    user_key = post_data['idUser']
    html_code = post_data['htmlString']

    html_code = urllib.unquote(html_code.replace("\t", "").replace("\n", ""))
    relevant_properties = process_html_page(html_code)
    mongo.register_html(url, user_key, html_code, relevant_properties)

    return HttpResponse()

def process_html_page(html_code):
    """
    Process html code and gets relevant properties
    """
    properties_list = []

    # Retrieve important meta properties
    meta_tags = re.findall("<meta.*?>", html_code)
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
