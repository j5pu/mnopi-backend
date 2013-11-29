# coding=utf-8
from django.shortcuts import render, render_to_response

from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

import urlparse
import json
import simplejson

from models import User, PageVisited, Search, UserCategorization, CategorizedDomain
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

CURRENT_VERSION = "alpha2"

#TODO: Volver a poner y tratar el tema de csrf

def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('mnopi.views.dashboard'))
    else:
        return render(request, 'mnopi/index.html')

def login_user(request):
    #TODO: incorporar checkeos javascript en interfaces

    def login_failed(message):
        return render(request, 'mnopi/index.html', {'error_message': message})

    try:
        username = request.POST['user_key']
        password = request.POST['password']
    except(KeyError):
        return login_failed(LOGIN_FIELDS_ERROR)

    if username == "" or password == "":
        return login_failed(LOGIN_FIELDS_ERROR)

    user = authenticate(username=username, password=password)
    if user is not None and user.is_active:
        login(request, user)
        return HttpResponseRedirect(reverse('mnopi.views.dashboard'))
    else:
        return login_failed(LOGIN_BAD_PASSWORD)

@csrf_exempt
def plugin_login(request):
    # TODO: investigar si seguridad puede conseguir con el login de Django
    try:
        username = request.POST['user_key']
        password = request.POST['password']
        version = request.POST['version']
    except(KeyError):
        return HttpResponse("err")

    if version != CURRENT_VERSION: #TODO: Constantizar en un fichero como dios manda
        return HttpResponse("version_error")
    user = authenticate(username=username, password=password)
    if user is not None and user.is_active:
        return HttpResponse("ok")
    else:
        return HttpResponse("err")

def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse('mnopi.views.index'))

def register(request):
    return render(request, 'mnopi/register.html')

def conditions(request):
    return render(request, 'mnopi/conditions.html')

def plugin(request):
    return render(request, 'mnopi/plugin.html')

def new_user(request):
    """
    Signs up a user to the system. It checks every parameter
    """

    def registration_failed(message):
        return render(request, 'mnopi/register.html', {'error_message' : message})

    try:
        username = request.POST['user_key']
        password = request.POST['password']
        password_repeat = request.POST['confirm']
    except(KeyError):
        return registration_failed(REGISTRATION_FIELDS_ERROR)

    if username == "":
        return registration_failed(REGISTRATION_USER_EMPTY)
    elif password != password_repeat:
        return registration_failed(REGISTRATION_PASSWORDS_DONT_MATCH)
    elif len(password) < PASS_MIN_LENGTH:
        return registration_failed(REGISTRATION_PASSWORD_ERROR)
    elif not request.POST.get('acceptance', False):
        return registration_failed(REGISTRATION_CONDITIONS_ERROR)
    if User.objects.filter(username=username).count() != 0:
        return registration_failed(REGISTRATION_USER_EXISTS)

    User.objects.create_user(username=username, password=password)

    return render(request, 'mnopi/register_successful.html')

@csrf_exempt
def page_visited(request):
    """
    Registers an url visited by the user, updating data for its corresponding categories
    """

    post_data = json.loads(request.body)
    url = post_data['url']
    username = post_data['idUser']

    url_domain = urlparse.urlparse(url)[1]
    categories = opendns.getCategories(url_domain)

    user = User.objects.get(username=username)
    categorized_domain = CategorizedDomain.objects.get(domain=url_domain)
    PageVisited.objects.create(user=user, page_visited=url, domain=categorized_domain)
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
    username = post_data['idUser']

    user = User.objects.get(username=username)
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
    username = post_data['idUser']
    html_code = post_data['htmlString']

    # Automatic keywords mining is performed when creating the object
    models_mongo.register_html_visited(page_visited=url, html_code=html_code, user=username)

    return HttpResponse()

@login_required
def user_keywords(request, username):
    """
    Returns the keywords associated with an user
    """
    #TODO: tentative name and function

    user = User.objects.get(username=username)
    words = user.get_keywords_freqs_from_properties(50)
    resp = simplejson.dumps(words) #TODO: reducir numero de palabras enviadas

    return HttpResponse(resp, mimetype='application/json')

@login_required
def profiler(request):
    """
    Shows categories visited by the user and the pages comprised by the categories
    """

    user = get_object_or_404(User, username=request.user.username)
    domains_by_category = user.get_domains_by_category()

    resp = {'domains_by_category': domains_by_category}

    return render_to_response("mnopi/profiler.html", resp, context_instance=RequestContext(request))

@login_required
def dashboard(request):
    """
    View that retrieves data and shows dashboard to user
    """
    def extend_freqs(freqs):
        words = []
        for word in freqs:
            for i in range(0, word[1]):
                words.append(word[0])

        return words

    user = get_object_or_404(User, username=request.user.username)
    visits_by_category_list = user.get_visits_by_category()

    metadata_keywords = user.get_keywords_freqs_from_properties(30)
    metadata_keywords = extend_freqs(metadata_keywords)

    site_keywords = user.get_keywords_freqs_from_html(30) #TODO: constantizar
    site_keywords = [{'keyword': x, 'frequency': y} for (x, y) in site_keywords]

    last_searches = [search.search_query for search in
                     Search.objects.filter(user=user).order_by('-date')[0:4]]
    last_pages = [page.page_visited for page in
                  PageVisited.objects.filter(user=request.user).order_by('-date')[0:12]]

    resp = {'visits_by_category': simplejson.dumps(visits_by_category_list),
            'metadata_keywords': simplejson.dumps(metadata_keywords),
            'site_keywords': simplejson.dumps(site_keywords),
            'last_searches': last_searches,
            'last_pages': last_pages}

    return render_to_response("mnopi/dashboard.html", resp, context_instance=RequestContext(request))

class UserPagesVisitedList(ListView):

    template_name = 'mnopi/pages_visited.html'
    context_object_name = 'pages_visited'
    paginate_by = 25

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserPagesVisitedList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.request.user.username)
        if 'limit' in self.kwargs:
            return PageVisited.objects.filter(user=self.user).order_by('-date')[0:int(self.kwargs['limit'])]
        else:
            return PageVisited.objects.filter(user=self.user).order_by('-date')


class UserSearchesDoneList(ListView):

    template_name = 'mnopi/searches_done.html'
    context_object_name = 'searches_done'
    paginate_by = 25

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserSearchesDoneList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.request.user.username)
        if 'limit' in self.kwargs:
            return Search.objects.filter(user=self.user).order_by('-date')[0:int(self.kwargs['limit'])]
        else:
            return Search.objects.filter(user=self.user).order_by('-date')

class UserSiteKeywordsList(ListView):

    KEYWORDS_LIMIT = 200

    template_name = 'mnopi/site_keywords.html'
    context_object_name = 'site_keywords'
    paginate_by = 25

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserSiteKeywordsList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.request.user.username)
        site_keywords = self.user.get_keywords_freqs_from_html(
            UserSiteKeywordsList.KEYWORDS_LIMIT)
        site_keywords = [{'keyword': x, 'frequency': y} for (x, y) in site_keywords]
        return site_keywords

class UserMetaKeywordsList(ListView):
    """
    List of metadata (meta description, title, meta keywords) keywords, obtained
    from meta html attributes
    """

    KEYWORDS_LIMIT = 200

    template_name = 'mnopi/meta_keywords.html'
    context_object_name = 'meta_keywords'
    paginate_by = 25

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserMetaKeywordsList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.request.user.username)
        meta_keywords = self.user.get_keywords_freqs_from_properties(
            UserMetaKeywordsList.KEYWORDS_LIMIT)
        meta_keywords = [{'keyword': x, 'frequency': y} for (x, y) in meta_keywords]
        return meta_keywords


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
