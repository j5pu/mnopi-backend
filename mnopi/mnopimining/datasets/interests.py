from nltk.stem.snowball import SnowballStemmer

def stem_dictionary_keys(d, language='english'):
    """
    Stems the keys in a dictionary whose keys are words
    """
    stemmer = SnowballStemmer(language)
    return {stemmer.stem(k): v for (k, v) in d.items()}


BUY_INTENTION_WORDS_ES = {
    'comprar': 1,
    'comparativa': 1,
    'barato': 1,
    'precio': 1,
    'regalo': 1,
    'mejores': 1,
    'recomendacion': 1,
    'calidad': 0.5,
    'tiendas': 0.5,
    'saldo': 0.5,
    'amazon': 1,
    'ebay': 1,
    'chollo': 1,
    'opinion': 1,
    'descuento': 1,
    'venta': 1,
    'outlet': 1,
    'disponibilidad': 1,
    'stock': 1,
    'bueno': 1,
    'valoracion': 1,
    'economico': 1,
    'ofertas': 1,
    'promociones': 1,
    'rebajas': 1,
    'marcas': 1,
    'caro': 1,
    'liquidacion': 1,
    'sales': 1,
}

TRAVEL_INTENTION_WORDS_ES = {
    'viaje': 1,
    'tours': 1,
    'hotel': 1,
    'hostal': 1,
    'mapa': 1,
    'guia': 1,
    'que ver': 1,
    'como ir': 1,
    'turismo': 1,
    'como llegar': 1,
    'viajar': 1,
    'museos': 1,
    'atracciones': 1,
    'aeropuertos': 1,
    'tren': 1,
    'restaurante': 1,
    'playa': 1,
    'vuelo': 1,
    'low-cost': 1,
    'transportes': 1,
    'aventura': 1,
    'temporada': 1,
    'monumentos': 1,
    'rutas': 1,
    'vacaciones': 1,
    'crucero': 1,
}

# TODO: add groups of words

LEXICAL_BUY_INTENTION_ES = stem_dictionary_keys(BUY_INTENTION_WORDS_ES, 'spanish')
LEXICAL_TRAVEL_INTENTION_ES = stem_dictionary_keys(TRAVEL_INTENTION_WORDS_ES, 'spanish')