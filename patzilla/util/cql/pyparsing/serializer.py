# -*- coding: utf-8 -*-
# (c) 2014-2016 Andreas Motl, Elmyra UG
import re
import types
import logging
import StringIO
from pyparsing import ParseResults
from patzilla.util.cql.pyparsing.parser import CQLGrammar
from patzilla.util.cql.pyparsing.util import walk_token_results, token_to_triple
from patzilla.util.cql.knowledge import indexes_publication_number
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.util.data.convert import shrink_list

log = logging.getLogger(__name__)

grammar = CQLGrammar()

def parse_cql(cql):
    """
    Helper function for doctests
    """
    from . import CQL
    c = CQL(cql)
    return c.parse()

def tokens_to_cql(tokens):
    """
    Reproduce CQL query string from parsed tokens

    >>> tokens = parse_cql('foo=bar and baz=(qux or quux)')
    >>> tokens_to_cql(tokens)
    u'foo=bar and baz=(qux or quux)'

    """
    buffer = StringIO.StringIO()
    tokens_to_cql_buffer(tokens, buffer)
    buffer.seek(0)
    return buffer.read()

def tokens_to_cql_buffer(tokens, buffer):
    """Reproduce CQL query string from parsed tokens, worker"""
    for token in tokens:
        tokentype = type(token)

        if tokentype is ParseResults:
            name = token.getName()
            if name.startswith('triple'):
                triple = token_to_triple(token)
                if triple:
                    index, binop, term = triple

                    # surround binop with spaces for all operators but equality (=)
                    if binop != '=':
                        triple[1] = u' {0} '.format(binop)

                    payload = u''.join(triple)

                else:
                    payload = u''.join(token)

                buffer.write(payload)

            elif name.startswith('subquery'):
                tokens_to_cql_buffer(token, buffer)

        elif tokentype in types.StringTypes:
            out = token
            # surround all boolean operators with whitespace
            if token in grammar.booleans:
                out = u' {0} '.format(token)
            buffer.write(out)

def normalize_patentnumbers(tokens):
    """
    normalize patent numbers in query

    >>> tokens = parse_cql('pn=EP666666')
    >>> normalize_patentnumbers(tokens)
    >>> tokens_to_cql(tokens)
    u'pn=EP0666666'

    """
    def action(token, index, binop, term):
        term = term.replace('"', '')
        # apply document number normalization to values of certain indexes only
        if index.lower() in indexes_publication_number:
            term = normalize_patent(term, fix_kindcode=True)
            if term:
                token[2] = term

    walk_token_results(tokens, triple_callback=action)

def get_keywords(triples, whitelist_indexes=None):
    """
    compute list of keywords

    >>> triples = []; get_triples(parse_cql('txt=foo or (bi=bar or bi=baz)'), triples)
    >>> get_keywords(triples)
    [u'foo', u'bar', u'baz']

    >>> triples = []; get_triples(parse_cql('pa all "central, intelligence, agency"'), triples)
    >>> get_keywords(triples)
    [u'central', u'intelligence', u'agency']

    >>> triples = []; get_triples(parse_cql('foo=bar and baz=qux'), triples)
    >>> get_keywords(triples, ['baz'])
    [u'qux']

    """
    keywords = []
    for triple in triples:
        try:
            index, binop, term = triple
            index_allowed = (not whitelist_indexes) or (index in whitelist_indexes) or (index.lower() in whitelist_indexes)
            if index_allowed:
                # for "any" or "all" relations ...
                if binop in ['any', 'all']:
                    # strip single and double quotes from term
                    # split by comma or whitespace
                    # iterate subterms
                    for subterm in re.split('(?:,\s|,|\s)', term.strip('"\'')):
                        keywords.append(subterm)
                else:
                    keywords.append(term)
        except ValueError as ex:
            # TODO: Is it okay just passing on this exception?
            pass

    keywords = trim_keywords(keywords)

    return keywords

def trim_keywords(keywords):
    """
    trim list of keywords

    - split search term by any term operator symbol
    - strip wildcard characters from each keyword element
    - reconstruct a list of keywords with simple scalars for single-term
      keywords and a list of keyword elements for multi-term keywords

    Example:
    >>> trim_keywords([u'!!!daimler?', u'Misch?(P)?wasser'])
    [u'daimler', [u'Misch', u'wasser']]

    >>> trim_keywords([u'"foo"', u'"   bar   "'])
    [u'foo', u'bar']

    """
    keywords_trimmed = []
    stripchars = grammar.wildcards + '"\'() '
    for keyword in keywords:
        matches = re.split(grammar.termop.pattern, keyword, flags=grammar.termop.flags)
        matches = [match.strip(stripchars) for match in matches]
        keywords_trimmed.append(shrink_list(matches))
    return keywords_trimmed

def get_triples(tokens, triples):
    """
    compute flattened list of triples

    >>> triples = []; get_triples(parse_cql('foo=bar and baz=(qux or quux)'), triples)
    >>> triples
    [['foo', u'=', 'bar'], ['qux'], ['quux']]

    """
    for token in tokens:
        tokentype = type(token)
        if tokentype is ParseResults:
            name = token.getName()
            if name.startswith('triple'):
                triple = token_to_triple(token) or list(token)
                triples.append(triple)
            elif name.startswith('subquery'):
                get_triples(token, triples)

def expand_shortcut_notation(tokens, index=None, binop=None):
    """
    Expand value shortcut notations like 'index=(term)' or 'index=(term1 and term2 or term3)'

    >>> tokens = parse_cql('foo=bar and baz=(qux or quux)')
    >>> expand_shortcut_notation(tokens)
    >>> tokens_to_cql(tokens)
    u'foo=bar and (baz=qux or baz=quux)'

    """
    for token in tokens:
        tokentype = type(token)

        if tokentype is ParseResults:
            name = token.getName()

            if name == 'triple-short':

                # HACK / workaround:
                # Check whether term contains neighbourhood operators.
                # If it does, put term inside parenthesis, which got lost while performing shortcut expansion.
                if token:
                    if re.match('.*(?:' + grammar.termop.pattern + ').*', token[0], flags=grammar.termop.flags):
                        token[0] = u'({0})'.format(token[0])

                # Process triple in value shortcut notation (contains only the single term).
                # Take action: Insert index and binop from subquery context.
                if index and binop:
                    token.insert(0, binop)
                    token.insert(0, index)

            elif name == 'subquery':
                expand_shortcut_notation(token, index, binop)

            elif name == 'subquery-short':
                # Dive into a subquery containing values in shortcut notation.
                # Remember index and binop for nested triple processing.
                index_ = token.pop(0)
                binop_ = token.pop(0)
                expand_shortcut_notation(token, index_, binop_)
