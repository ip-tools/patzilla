# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
#
# CQL grammar based on pyparsing
# https://en.wikipedia.org/wiki/Contextual_Query_Language
#
# Derived from simpleSQL.py, Copyright (c) 2003, Paul McGuire
# http://pyparsing.wikispaces.com/file/view/simpleSQL.py
#
# See also:
#
# - http://pyparsing.wikispaces.com/HowToUsePyparsing
# - http://pyparsing.wikispaces.com/file/view/searchparser.py
# - http://pyparsing-public.wikispaces.com/file/view/aql.py
#
import re
import logging
from pyparsing import \
    Word, \
    Literal, CaselessLiteral, \
    Keyword, CaselessKeyword, \
    Regex, \
    alphas, nums, alphanums, quotedString, \
    oneOf, upcaseTokens, delimitedList, restOfLine, \
    Forward, Group, Combine, Optional, ZeroOrMore, OneOrMore, \
    NotAny, Suppress, FollowedBy, StringEnd, \
    ParseResults, ParseException, removeQuotes
from patzilla.util.cql.pyparsing.util import get_literals


log = logging.getLogger(__name__)


# ------------------------------------------
#   A. characters
# ------------------------------------------

"""
Truncation / Wildcards

OPS - see `Open Patent Services RESTful Web Services Reference Guide`_, p. 149::

    7. A word might contain truncation characters:
    • unlimited truncation (*) which represents a string of any length including any character,
    • limited truncation (?) which represents any character or no character,
    • masking truncation (#) which represents any character which is mandatory present,
    • it is possible to use truncation at the beginning of a word.

DEPATISnet - see `DEPATISnet Expert mode guide`_::

    ?   no characters to any number of characters
    !   precisely one character
    #   zero or one character

TODO: maybe extract this to a different place, since ..services is also using it
"""
wildcards = u'*?#!'

# - classification terms (IPC, CPC) may contain forward slashes and dashes, e.g. H04L12/433, F17D5-00
# - numeric terms may contain punctuation (,.), e.g. 2.45
# - dates may contain dashes, e.g. M11-2009
separators = u'/,.-'

# limited set of unicode characters
#umlauts = u'äöüÄÖÜß'

# all unicode characters
# http://stackoverflow.com/questions/2339386/python-pyparsing-unicode-characters/2340659#2340659
unicode_printables = u''.join(unichr(c) for c in xrange(65536) if unichr(c).isalnum() and not unichr(c).isspace())

# indexchars
indexchars = alphanums + '{}!'


# ------------------------------------------
#   B. symbols
# ------------------------------------------

class CQLGrammar(object):

    # Various sets of characters
    wildcards  = wildcards
    separators = separators
    unicode_printables = unicode_printables

    def __init__(self):
        self.parser = None
        self.preconfigure()
        self.configure()
        self.build()

    def preconfigure(self):

        # Binary comparison operators
        self.cmp_single = u'= != < > <= >='.split()
        self.cmp_perl = u'eq ne lt gt le ge'.split()
        self.cmp_cql = u'exact within encloses all any any/relevant any/rel.lr'.split()

        # Boolean operators
        # TODO: Configure german operators with DPMAGrammar only
        self.and_ = CaselessKeyword("and") | CaselessKeyword("UND")
        self.or_ = CaselessKeyword("or") | CaselessKeyword("ODER")
        self.not_ = CaselessKeyword("not") | CaselessKeyword("NICHT")
        self.prox_ = CaselessKeyword("prox") | CaselessKeyword("NAHE")

        # Neighbourhood term operators
        self.neighbourhood_symbols = '(W) (NOTW) (#W) (A) (#A) (P) (L)'.split()

    def configure(self):

        # Binary comparison operators
        self.binop_symbols = self.cmp_single + self.cmp_perl + self.cmp_cql

        # Boolean operators
        self.booleans    = get_literals(self.and_, self.or_, self.not_, self.prox_)
        self.booleans_or = ( self.and_ | self.or_ | self.not_ | self.prox_ )

        # Neighbourhood term operators
        # see also:
        # - https://depatisnet.dpma.de/depatisnet/htdocs/prod/de/hilfe/recherchemodi/experten-recherche/
        # - https://depatisnet.dpma.de/depatisnet/htdocs/prod/en/hilfe/recherchemodi/experten-recherche/

        # v1: this would work for simple term operators only
        #self.termop = oneOf(self.neighbourhood_symbols, caseless=True).setName("termop")

        # v2: use regexes for describing term operators like "(10A)"
        self.neighbourhood_symbols = [
            '\s?' + re.escape(symbol).replace('\#', '\d+') + '\s?'
            for symbol in self.neighbourhood_symbols
        ]

    def build(self):

        # ------------------------------------------
        #   C. building blocks
        # ------------------------------------------
        self.termop = Regex( "|".join(self.neighbourhood_symbols), re.IGNORECASE ).setParseAction( upcaseTokens ).setName("termop")
        termword = Word(self.unicode_printables + self.separators + self.wildcards).setName("term")
        termword_termop = (termword + OneOrMore( self.termop + termword ))


        # ------------------------------------------
        #   D. triple
        # ------------------------------------------

        index = Word(alphanums).setName("index")

        #index = Word(indexchars).setName("index")
        #SolrProximitySuffix = Suppress(Optional(Word('~') + Word(nums)))

        binop = oneOf(self.binop_symbols, caseless=True).setName("binop")
        term = (

            # Attempt to parse {!complexphrase}text:"((aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*))"~6 ...
            # ... but failed.
            #Combine(quotedString.setParseAction(removeQuotes) + SolrProximitySuffix).setName("term") ^

            # term is a quoted string, easy peasy
            quotedString.setName("term") ^

            # term is just a termword, easy too
            termword.setName("term") ^

            # term contains neighbourhood operators, so should have been wrapped in parenthesis
            Combine('(' + Suppress(ZeroOrMore(' ')) + termword_termop + Suppress(ZeroOrMore(' ')) + ')').setName("term") ^

            # convenience/gracefulness: we also allow terms containing
            # neighbourhood operators without being wrapped in parenthesis
            Combine(termword_termop).setName("term")

        )


        # ------------------------------------------
        #   E. condition
        # ------------------------------------------
        cqlStatement = Forward()

        # Parse regular cql condition notation 'index=term'.
        cqlConditionBase = Group(

            # a regular triple
            ( index + binop + term ).setResultsName("triple") |

            # a regular subquery
            ( "(" + cqlStatement + ")" ).setResultsName("subquery")
        )

        # Parse value shortcut notations like 'index=(term)' or 'index=(term1 and term2 or term3)'.
        cqlConditionShortcut = Group(

            # a triple in value shortcut notation (contains only the single term)
            # "term + NotAny(binop)" helps giving proper error messages like
            # "ParseException: Expected term (at char 4)" for erroneous queries like "foo="
            ( term + NotAny(binop) ).setResultsName("triple-short") |

            # a subquery containing values in shortcut notation
            ( index + binop + "(" + cqlStatement + ")" ).setResultsName("subquery-short")

        )

        #cqlCondition = cqlConditionBase
        cqlCondition = cqlConditionBase | cqlConditionShortcut


        # ------------------------------------------
        #   F. statement
        # ------------------------------------------

        cqlStatement << cqlCondition + ZeroOrMore( self.booleans_or + cqlStatement )

        # apply SQL comment format
        cqlComment = "--" + restOfLine
        cqlStatement.ignore(cqlComment)

        self.parser = cqlStatement
