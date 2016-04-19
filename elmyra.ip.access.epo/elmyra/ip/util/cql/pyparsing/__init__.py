# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import pyparsing
from parser import parse_cql
from serializer import tokens_to_cql, expand_shortcut_notation, get_triples, get_keywords, normalize_patentnumbers

class CQL(object):

    def __init__(self, cql=None, logging=True, keyword_fields=None):
        self.logging = logging
        self.keyword_fields = keyword_fields or []
        self.tokens = []
        if cql:
            self.loads(cql)

    def loads(self, cql, strip=True):
        if strip:
            cql = cql.strip()
        self.cql = cql
        self.tokens = parse_cql(self.cql, self.logging)

    def dumps(self):
        return tokens_to_cql(self.tokens)

    def triples(self):
        triples = []
        get_triples(self.tokens, triples)
        return triples

    def keywords(self):
        return get_keywords(self.triples(), self.keyword_fields)

    def expand_shortcuts(self):
        expand_shortcut_notation(self.tokens)
        return self

    def normalize_numbers(self):
        normalize_patentnumbers(self.tokens)
        return self

    def polish(self):
        return self.expand_shortcuts().normalize_numbers()


# Monkeypatch flaw in pyparsing

def pyparsing_parseresults_pop_fixed( self, *args, **kwargs):
    """Removes and returns item at specified index (default=last).
       Supports both list and dict semantics for pop(). If passed no
       argument or an integer argument, it will use list semantics
       and pop tokens from the list of parsed tokens. If passed a
       non-integer argument (most likely a string), it will use dict
       semantics and pop the corresponding value from any defined
       results names. A second default return value argument is
       supported, just as in dict.pop()."""
    if not args:
        args = [-1]
    if 'default' in kwargs:
        args.append(kwargs['default'])
    if (isinstance(args[0], int) or
        len(args) == 1 or
        args[0] in self):

        # TODO: send this fix upstream!
        index = int(args[0])

        ret = self[index]
        del self[index]
        return ret
    else:
        defaultvalue = args[1]
        return defaultvalue

pyparsing.ParseResults.pop = pyparsing_parseresults_pop_fixed
