# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from elmyra.ip.util.cql import cheshire3_parser
from elmyra.ip.util.cql.cheshire3_parser import SearchClause
from elmyra.ip.util.numbers.normalize import normalize_patent

class SmartSearchClause(SearchClause):
    """
    Will make query a bit smarter. By now, it mainly intercepts "pn=" attributes
    by sending the values through a document number normalization subsystem.
    """

    def toCQL(self):

        text = []
        for p in self.prefixes.keys():
            if (p <> ''):
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

        text.append('%s %s "%s"' % (self.index,
                                    self.relation.toCQL(),
                                    term))
        # Add sortKeys
        if self.sortKeys:
            text.append("sortBy")
            for sk in self.sortKeys:
                text.append(sk.toCQL())
        return ' '.join(text)

        return SearchClause.toCQL(self)

# modify default behavior
cheshire3_parser.searchClauseType = SmartSearchClause
cheshire3_parser.serverChoiceIndex = ''
cheshire3_parser.serverChoiceRelation = ''
