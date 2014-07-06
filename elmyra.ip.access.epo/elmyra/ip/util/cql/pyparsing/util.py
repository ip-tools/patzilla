# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
from pyparsing import ParseResults

def get_literals(*elements):
    literals = []
    for element in elements:
        for literal in element:
            literal = unicode(literal).strip('"').strip("'")
            literals.append(literal)
    return literals

def walk_token_results(tokens, *args, **kwargs):

    for token in tokens:
        tokentype = type(token)
        if tokentype is ParseResults:
            name = token.getName()
            if name.startswith('triple'):
                triple = list(token)

                if len(triple) == 3:
                    index, binop, term = triple

                    if 'triple_callback' in kwargs:
                        kwargs['triple_callback'](token, index, binop, term)

            elif name.startswith('subquery'):
                walk_token_results(token, *args, **kwargs)
