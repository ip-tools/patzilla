# -*- coding: utf-8 -*-
# (c) 2014-2016 Andreas Motl, Elmyra UG
import re

_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_strip_wo_equals_re = re.compile(r'[^\w\s=-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')
def slugify(value, strip_equals=True, lowercase=True):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".

    Via http://code.activestate.com/recipes/577257-slugify-make-a-string-usable-in-a-url-or-filename/
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')

    _strip_re = _slugify_strip_re
    if not strip_equals:
        _strip_re = _slugify_strip_wo_equals_re
    value = unicode(_strip_re.sub('', value).strip())

    if lowercase:
        value = value.lower()

    value =  _slugify_hyphenate_re.sub('-', value)
    return value

def text_indent(text, amount=4, ch=' '):
    # https://stackoverflow.com/questions/8234274/how-to-indent-the-content-of-a-string-in-python/8348914#8348914
    padding = amount * ch
    return padding + ('\n' + padding).join(text.split('\n'))
