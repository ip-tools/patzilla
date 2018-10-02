# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import re
import logging

import attr

from patzilla.util.cql.pyparsing import CQL
from patzilla.util.cql.util import should_be_quoted
from patzilla.util.python import _exception_traceback
from patzilla.util.data.container import unique_sequence
from patzilla.util.expression.keywords import clean_keyword, compute_keywords

logger = logging.getLogger(__name__)


@attr.s
class SearchExpression(object):

    syntax = attr.ib(default='cql')
    grammar = attr.ib(default=None)
    keyword_fields = attr.ib(default=None)

    expression = attr.ib(default=None)
    cql_parser = attr.ib(default=None)
    keywords = attr.ib(default=attr.Factory(list))
    keywords_origin = attr.ib(default=None)

    def parse_expression(self, query):

        logger.info(u'Parsing search expression "{query}" with syntax "{syntax}" and grammar "{grammar}"'.format(
            query=query, syntax=self.syntax, grammar=self.grammar and self.grammar.__name__ or u'default'))

        if self.syntax == 'cql':
            self.parse_expression_cql(query)

        elif self.syntax == 'ikofax':
            self.parse_expression_ikofax(query)

    def parse_expression_cql(self, expression):

        # Fixup query: Wrap into quotes if CQL expression is a) unspecific, b) contains spaces and c) is still unquoted
        if should_be_quoted(expression) and u'within' not in expression:
            expression = u'"%s"' % expression

        # Parse and recompile CQL query string to apply number normalization
        query_object = None
        try:

            # v1: Cheshire3 CQL parser
            #query_object = cql_parse(query)
            #query = query_object.toCQL().strip()

            # v2 pyparsing CQL parser
            query_object = CQL(expression, grammar=self.grammar, keyword_fields=self.keyword_fields).polish()
            query_recompiled = query_object.dumps()

            if query_recompiled:
                expression = query_recompiled

            if query_recompiled != expression:
                logger.info(u'Recompiled search expression to "{query}"'.format(query=expression))

        except Exception as ex:
            # TODO: Can we get more details from diagnostic information to just stop here w/o propagating obviously wrong query to OPS?
            logger.warn(u'CQL parse error: query="{0}", reason={1}, Exception was:\n{2}'.format(expression, ex, _exception_traceback()))

        self.cql_parser = query_object
        self.expression = expression

        if query_object:

            keywords = []
            try:
                keywords = query_object.keywords()
                self.keywords_origin = 'grammar'

            except AttributeError:
                keywords = compute_keywords(query_object)
                self.keywords_origin = 'compute'

            # List of keywords should contain only unique items
            self.keywords = unique_sequence(keywords)

    def parse_expression_ikofax(self, expression):
        words_raw = re.split('(\s+)', expression)
        words = []
        stopwords = ['and', 'or', 'not']
        badchars = '()?!#\''
        for word in words_raw:
            word = word.strip()
            if not word: continue
            if word.lower() in stopwords: continue
            word = word.split('/')[0]
            word = clean_keyword(word.strip(badchars))
            if len(word) <= 3: continue
            words.append(word)

        self.cql_parser = None
        self.expression = expression
        self.keywords = unique_sequence(words)
        self.keywords_origin = 'heuristic'
