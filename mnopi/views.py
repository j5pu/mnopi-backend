# coding=utf-8

from django.shortcuts import render, render_to_response

from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from hashlib import sha256 # TODO: Check better security options
import urlparse
import json
import simplejson

from models import User, PageVisited, Search, UserCategorization
import models_mongo
import opendns
from mnopimining import users

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


#TODO: Volver a poner y tratar el tema de csrf

def index(request):
    return render(request, 'mnopi/index.html')

@csrf_exempt
def login(request):
    #TODO: cambiar utilizando el sistema de Django
    #TODO: incorporar checkeos javascript en interfaces
    #TODO: separar el servicio de entrada desde plugin y desde web. Interfaz rest?

    def login_failed(message):
        return render(request, 'mnopi/index.html', {'error_message': message}, status=212)

    try:
        user_key = request.POST['user_key']
        password = request.POST['password']
    except(KeyError):
        return login_failed(LOGIN_FIELDS_ERROR)

    if user_key == "" or password == "":
        return login_failed(LOGIN_FIELDS_ERROR)
    # elif not mongo.user_exists(user_key):
    #     return login_failed(LOGIN_USER_DOESNT_EXIST)
    #TODO: AUTENTICACION

    user = User.objects.get(user_key=user_key)
    # elif not mongo.authenticate_user(user_key, password):
    #     return login_failed(LOGIN_BAD_PASSWORD)

    return render(request, 'mnopi/main.html')


def register(request):
    return render(request, 'mnopi/register.html')

def conditions(request):
    return render(request, 'mnopi/conditions.html')

def new_user(request):
    """
    Signs up user to the system. It checks every parameter
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
    # TODO: Autenticacion
    # elif mongo.user_exists(user_key):
    #     return render(request, 'mnopi/register.html', {'error_message' : REGISTRATION_USER_EXISTS})

    hashed_password = sha256(password).hexdigest()
    User.objects.create(user_key=user_key, password=hashed_password)
    # mongo.add_user(user_key, password)

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

    user = User.objects.get(user_key=user_key)
    PageVisited.objects.create(user=user, page_visited=url)
    user.update_categories_visited(categories)

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

    user = User.objects.get(user_key=user_key)
    Search.objects.create(search_query=search_query,
                          search_results=search_results,
                          user=user)

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

    # Automatic keywords mining is performed when creating the object
    models_mongo.register_html_visited(page_visited=url, html_code=html_code, user=user_key)

    # relevant_properties = get_html_metadata(html_code)
    #
    # keywords_freqs = {}
    # keywords_freqs['text'] = keywords.get_freq_words(nltk.clean_html(html_code))
    # keywords_freqs['metadata'] = keywords.get_freq_words(" ".join([x[1] for x in relevant_properties]))
    #
    # mongo.register_html(url, user_key, html_code, relevant_properties, keywords_freqs)

    return HttpResponse()


def user_keywords(request, user_key):
    """
    Returns the keywords associated with an user
    """
    #TODO: tentative name and function

    user = User.objects.get(user_key=user_key)
    words = user.get_keywords_freqs_from_properties(50)
    resp = simplejson.dumps(words) #TODO: reducir numero de palabras enviadas

    return HttpResponse(resp, mimetype='application/json')

def dashboard(request, user_key):
    """
    View that retrieves data and shows dashboard to user
    """
    def extend_freqs(freqs):
        words = []
        for word in freqs:
            for i in range(0, word[1]):
                words.append(word[0])

        return words

    user = User.objects.get(user_key=user_key)
    categories = user.categories.all()
    visits_by_category = [UserCategorization.objects.get(user=user, category=cat).weigh for cat in categories]
    #TODO: Falta por meter errores
    visits_by_category_list = [{'category': x.name, 'visits': y} for (x, y) in zip(categories, visits_by_category)]

    metadata_keywords = user.get_keywords_freqs_from_properties(50)
    metadata_keywords = extend_freqs(metadata_keywords)

    site_keywords = user.get_keywords_freqs_from_html(30) #TODO: constantizar
    site_keywords = [{'keyword': x, 'frequency': y} for (x, y) in site_keywords]

    resp = {'visits_by_category': simplejson.dumps(visits_by_category_list),
            'metadata_keywords': simplejson.dumps(metadata_keywords),
            'site_keywords': simplejson.dumps(site_keywords)}

    return render_to_response("mnopi/dashboard.html", resp, context_instance=RequestContext(request))


class UserPagesVisitedList(ListView):

    template_name = 'mnopi/pages_visited.html'
    context_object_name = 'pages_visited'
    paginate_by = 25

    def get_queryset(self):
        self.user = get_object_or_404(User, user_key=self.args[0])
        return PageVisited.objects.filter(user=self.user)

    def get_context_data(self, **kwargs):
        context = super(UserPagesVisitedList, self).get_context_data(**kwargs)
        context['user_name'] = self.user.user_key
        return context

class UserSearchesDoneList(ListView):

    template_name = 'mnopi/searches_done.html'
    context_object_name = 'searches_done'
    paginate_by = 25

    def get_queryset(self):
        self.user = get_object_or_404(User, user_key=self.args[0])
        return Search.objects.filter(user=self.user)

    def get_context_data(self, **kwargs):
        context = super(UserSearchesDoneList, self).get_context_data(**kwargs)
        context['user_name'] = self.user.user_key
        return context


def test(request):
    """
    DUMMY method for test pages
    """
    def extend_freqs(freqs):
        words = []
        for word in freqs:
            for i in range(0, freqs[word]):
                words.append(word)

        return words


    words = users.get_user_keywords_from_properties("alfredo")
    words = extend_freqs(words)

    resp = simplejson.dumps(words) #TODO: reducir numero de palabras enviadas

    return render_to_response("mnopi/test_tags.html", {'words': resp}, context_instance=RequestContext(request))
