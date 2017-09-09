# -*- coding: utf-8 -*-
# (c) 2014-2016 Andreas Motl, Elmyra UG
import pprint
import logging
import pyparsing
from .serializer import tokens_to_cql, expand_shortcut_notation, get_triples, get_keywords, normalize_patentnumbers
from .parser import CQLGrammar

log = logging.getLogger(__name__)

class CQL(object):

    def __init__(self, cql='', grammar=None, logging=True, keyword_fields=None):
        self.cql = cql.strip()
        self.grammar = grammar or CQLGrammar
        self.logging = logging
        self.keyword_fields = keyword_fields or []
        self.tokens = self.parse()

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

    def parse(self):
        """
        Parse a CQL query string.

        >>> tokens = parse_cql('foo=bar')
        >>> tokens
        ([(['foo', u'=', 'bar'], {'triple': [((['foo', u'=', 'bar'], {}), 0)]})], {})

        """

        tokens = []

        if not self.cql:
            return tokens

        try:
            # make sure the whole query is parsed, otherwise croak
            tokens = self.grammar().parser.parseString(self.cql, parseAll=True)
            #if self.logging:
            #    log.info(u'tokens: %s', tokens.pformat())

        except pyparsing.ParseException as ex:
            ex.explanation = u'%s\n%s\n%s' % (ex.pstr, u' ' * ex.loc + u'^\n', ex)
            #if self.logging:
            #    log.error('\n%s', ex.explanation)
            log.warning(u'Query expression "{query}" is invalid. ' \
                        u'Reason: {reason}\n{location}'.format(
                query=self.cql, reason=unicode(ex), location=ex.explanation))
            raise

        return tokens


def parse_cql(cql):
    """
    Helper function for doctests
    """
    c = CQL(cql)
    return c.parse()


# Monkeypatch flaw in pyparsing

def pyparsing_parseresults_pop_fixed(self, *args, **kwargs):
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

def pyparsing_parseresults_pformat(self, *args, **kwargs):
    """
    Pretty-print formatter for parsed results as a list, using the C{pprint} module.
    Accepts additional positional or keyword args as defined for the
    C{pprint.pformat} method. (U{http://docs.python.org/3/library/pprint.html#pprint.pformat})
    """
    return pprint.pformat(self.asList(), *args, **kwargs)

pyparsing.ParseResults.pformat = pyparsing_parseresults_pformat
