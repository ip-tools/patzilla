# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
from . import CQL
from serializer import tokens_to_cql, expand_shortcut_notation, get_triples, get_keywords, normalize_patentnumbers

def parse_cql(cql):
    c = CQL(cql)
    return c.parse()

def enrich_cql(cql):
    tokens = parse_cql(cql)

    # B.1. enrich parsed model
    expand_shortcut_notation(tokens)
    normalize_patentnumbers(tokens)

    # B.3. dump all triples
    triples = []
    get_triples(tokens, triples)

    # B.4. dump all keywords
    keywords = get_keywords(triples)


def dump_results(tokens):
    cql = tokens_to_cql(tokens)
    print "=" * 42
    print "tokens:", tokens
    print "cql:", cql


def rundemo():
    tokens = None
    #tokens = parse_cql( 'foo' )
    #parse_cql( "foo=bar" )
    #parse_cql( "foo=bar and foo=baz" )
    #parse_cql( "foo bar" )
    #parse_cql( "foo=bar foo=baz" )
    #tokens = parse_cql( "foo=bar and (foo=baz or foo=qux)" )
    #tokens = parse_cql( "(foo=bar and foo=baz) or foo=qux" )
    #tokens = parse_cql( '(foo="bar" and foo="baz") or foo="qux"' )

    # shortcut notation
    #tokens = parse_cql( "foo=(bar and (baz or qux))" )
    #tokens = parse_cql( 'foo=(bar baz)' )
    #tokens = parse_cql( 'foo=("bar baz")' )
    #tokens = parse_cql( 'foo=(bar)' )

    # multiline queries with comments
    #tokens = parse_cql("""
    #foo=(bar and        -- comment 1
    #    (baz or qux))   -- comment 2
    #""")

    # real queries
    #tokens = parse_cql('txt=(greifer or gripper)')
    tokens = parse_cql('bi=(socke and (Inlay or Teile)) and pc=de')
    # pn=(EP0666666 or EP0666667)
    # pn=EP666666
    #tokens = parse_cql('pn=(EP666666 or EP666667)')
    #tokens = parse_cql('pa=(ibm) and pn=de')
    #tokens = parse_cql('BI=Socke und PA=onion')
    #tokens = parse_cql('ab=(L(W)Serine)')
    #tokens = parse_cql('ab=(L(w)Serine)')
    #tokens = parse_cql('ab=(L(W)Serine and treatment)')
    #tokens = parse_cql('ab=(serine and treatment)')

    if tokens:

        # A. show first stage parse (without modifications)
        dump_results(tokens)

        # B.1. enrich parsed model
        expand_shortcut_notation(tokens)
        normalize_patentnumbers(tokens)

        # B.2. dump enriched model
        dump_results(tokens)

        # B.3. dump all triples
        triples = []
        get_triples(tokens, triples)
        print "triples:", triples

        # B.4. dump all keywords
        keywords = get_keywords(triples)
        print "keywords:", keywords


if __name__ == '__main__':
    rundemo()
