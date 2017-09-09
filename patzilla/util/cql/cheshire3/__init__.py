# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import parser as cheshire3_parser
from parser import SearchClause, CQLParser, Diagnostic
from patzilla.util.numbers.normalize import normalize_patent


class SmartSearchClause(SearchClause):
    """
    Will make query a bit smarter. By now, it mainly intercepts "pn=" attributes
    by sending the values through a document number normalization subsystem.
    """

    def toCQL(self):

        text = []
        for p in self.prefixes.keys():
            if (p != ''):
                text.append('>%s="%s"' % (p, self.prefixes[p]))
            else:
                text.append('>"%s"' % (self.prefixes[p]))

        # add some smartness:

        # 1. for certain attributes, apply document number normalization to value
        term_vanilla = term = self.term.toCQL()
        if str(self.index).lower() in ['pn', 'num']:
            term = normalize_patent(str(term))

        # 2. fallback to original value, if number normalization couldn't handle this value
        if not term:
            term = term_vanilla

        # 3. exclude some values from being quoted (Error code: 1107 - Quote marks not applicable for this index)
        if str(self.index).lower() in ['pa', 'in', 'pc', 'ac', 'prc', 'py', 'ay', 'pry', 'pub', 'ad', 'prd']:
            pass
        else:
            term = '"%s"' % term

        text.append('%s %s %s' % (self.index,
                                    self.relation.toCQL(),
                                    term))
        # Add sortKeys
        if self.sortKeys:
            text.append("sortBy")
            for sk in self.sortKeys:
                text.append(sk.toCQL())
        return ' '.join(text)

        return SearchClause.toCQL(self)


class SmartCQLParser(CQLParser):
    """
    Will make query a bit smarter by allowing value shortcut notations
    like 'index=(term)' or 'index=(term1 and term2 or term3)'.
    """

    def subQuery(self):
        """
        Intercept subQuery method to apply subtriple expansion.
        """
        object = CQLParser.subQuery(self)
        object = self.expand_subtriples(object)
        return object

    def expand_subtriples(self, clause):
        """
        Expand subtriples gathered while building the search clause.
        """

        if not hasattr(clause, 'triples'):
            return clause

        triples = clause.triples
        while triples:
            trip = triples.pop(0)
            trip.leftOperand = clause
            trip.boolean.parent = clause
            trip.rightOperand.parent = clause
            clause = trip
        return clause

    def before_clause(self):
        # detect values in parentheses
        self.value_in_parentheses = False
        if (self.currentToken == '('):
            self.value_in_parentheses = True
            self.fetch_token()   # Skip Parenthesis

    def after_clause(self, irt):
        if self.value_in_parentheses:

            irt.triples = []

            # handle single-item values in parentheses like 'index=(term)'
            if self.currentToken == ')':
                self.fetch_token()   # Skip Parenthesis

            # handle multi-item values in parentheses like 'index=(term1 and term2 or term3)'
            # if we hit this, create more search clauses and triple envelopes reflecting the shortcut notation
            elif self.is_boolean(self.currentToken):

                # create objects holding information from value shortcut notation
                while True:

                    # Extract operator
                    operator = self.boolean()

                    # Extract Term
                    term = self.currentToken

                    # create new search clause
                    term = cheshire3_parser.termType(term)
                    irt_more = cheshire3_parser.searchClauseType(irt.index, irt.relation, term)

                    # create new triple
                    trip = cheshire3_parser.tripleType()
                    trip.boolean = operator
                    trip.rightOperand = irt_more

                    irt.triples.append(trip)


                    # Skip closing parenthesis
                    if self.nextToken == ')':
                        self.fetch_token()
                        self.fetch_token()
                        break

                    # Skip to next item of a multi-item value in parentheses
                    elif self.is_boolean(self.nextToken):
                        self.fetch_token()

                    else:
                        diag = Diagnostic()
                        diag.details = ("Expected Boolean or closing parenthesis but got: " +
                                        repr(self.nextToken))
                        raise diag


# modify default behavior
cheshire3_parser.booleans.extend(['und', 'oder', 'nicht', 'nahe'])
cheshire3_parser.CQLParser = SmartCQLParser
cheshire3_parser.searchClauseType = SmartSearchClause
cheshire3_parser.serverChoiceIndex = ''
cheshire3_parser.serverChoiceRelation = ''
