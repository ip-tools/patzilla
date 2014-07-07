# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import types
import StringIO
from pyparsing import ParseResults
from elmyra.ip.util.cql.pyparsing.parser import booleans, wildcards as wildcardchars
from elmyra.ip.util.cql.pyparsing.util import walk_token_results
from elmyra.ip.util.cql.knowledge import indexes_publication_number, indexes_keywords
from elmyra.ip.util.numbers.normalize import normalize_patent

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
                if len(token) == 3:
                    triple = list(token)
                    index, binop, term = triple

                    # surround binop with spaces for all operators but equality (=)
                    if binop != '=':
                        token[1] = u' {0} '.format(binop)

                buffer.write(u''.join(token))

            elif name.startswith('subquery'):
                tokens_to_cql_buffer(token, buffer)

        elif tokentype in types.StringTypes:
            out = token
            # surround all boolean operators with spaces
            if token in booleans:
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
        # apply document number normalization to values of certain indexes only
        if index.lower() in indexes_publication_number:
            term = normalize_patent(term)
            if term:
                token[2] = term

    walk_token_results(tokens, triple_callback=action)

def get_keywords(triples):
    """
    compute list of keywords

    >>> triples = []; get_triples(parse_cql('txt=foo or (bi=bar or bi=baz)'), triples)
    >>> get_keywords(triples)
    [u'foo', u'bar', u'baz']

    """
    keywords = []
    for triple in triples:
        try:
            index, binop, term = triple
            if index.lower() in indexes_keywords:
                keyword = term.strip(wildcardchars)
                keywords.append(keyword)
        except ValueError as ex:
            pass

    return keywords

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
                triples.append(list(token))
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
                index = token.pop(0)
                binop = token.pop(0)
                expand_shortcut_notation(token, index, binop)
