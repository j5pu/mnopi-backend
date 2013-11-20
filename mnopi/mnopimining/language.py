import langid
# TODO: ojo con licencia

LANGUAGE_NAMES =\
{
    "es": "spanish",
    "en": "english"
}


def detect_language(text):
    """
    Detects the language used in a given text.
    It returns a language identifier, which can be one of the following:

       af, am, an, ar, as, az, be, bg, bn, br, bs, ca, cs, cy, da, de, dz, el, en,
       eo, es, et, eu, fa, fi, fo, fr, ga, gl, gu, he, hi, hr, ht, hu, hy, id, is,
       it, ja, jv, ka, kk, km, kn, ko, ku, ky, la, lb, lo, lt, lv, mg, mk, ml, mn,
       mr, ms, mt, nb, ne, nl, nn, no, oc, or, pa, pl, ps, pt, qu, ro, ru, rw, se,
       si, sk, sl, sq, sr, sv, sw, ta, te, th, tl, tr, ug, uk, ur, vi, vo, wa, xh,
       zh, zu

    """

    # TODO: Eval performance, quiza sea mejor utilizar en algunos casos la url de la web si esta disponible (en plan .es)
    # TODO: otra opcion es utilizar solamente una pequenya parte del texto

    lang = langid.classify(text)[0]
    if lang in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[lang]
    else:
        return LANGUAGE_NAMES['en']