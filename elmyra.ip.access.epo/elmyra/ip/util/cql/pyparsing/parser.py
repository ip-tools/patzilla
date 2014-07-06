# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
#
# Derived from simpleSQL.py, Copyright (c) 2003, Paul McGuire
# http://pyparsing.wikispaces.com/file/view/simpleSQL.py
#
# http://pyparsing.wikispaces.com/HowToUsePyparsing
#
import logging
from pyparsing import \
    Word,\
    Literal, CaselessLiteral,\
    Keyword, CaselessKeyword,\
    alphas, nums, alphanums, quotedString, \
    Upcase, oneOf, delimitedList, restOfLine, \
    Forward, Group, Combine, Optional, ZeroOrMore, \
    NotAny, FollowedBy, StringEnd, \
    ParseResults, ParseException
from elmyra.ip.util.cql.pyparsing.util import get_literals


log = logging.getLogger(__name__)


# DEPATISnet uses "?!#"
# TODO: check OPS
wildcardchars = u'?!#'

# classification terms (IPC, CPC) may contain forward slashes
# numeric terms may contain punctuation (,.)
separatorchars = u'/,.'

# limited set of unicode characters
#umlautchars = u'äöüÄÖÜß'

# all unicode characters
# http://stackoverflow.com/questions/2339386/python-pyparsing-unicode-characters/2340659#2340659
unicode_printables = u''.join(unichr(c) for c in xrange(65536) if unichr(c).isalnum() and not unichr(c).isspace())

# define CQL grammar
index = Word(alphanums).setName("index")
binop = oneOf(u'= != < > <= >= eq ne lt gt le ge within encloses', caseless=True).setName("binop")
term  = ( Word(unicode_printables + separatorchars + wildcardchars).setName("term") ^ quotedString.setName("term") )

and_ = CaselessKeyword("and") | CaselessKeyword("und")
or_ = CaselessKeyword("or") | CaselessKeyword("oder")
not_ = CaselessKeyword("not") | CaselessKeyword("nicht")
prox_ = CaselessKeyword("prox") | CaselessKeyword("nahe")
booleans = get_literals(and_, or_, not_, prox_)

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
cqlStatement << cqlCondition + ZeroOrMore( ( and_ | or_ | not_ ) + cqlStatement )

# make sure the whole query is parsed, otherwise croak
cqlStatement += FollowedBy(StringEnd())

# apply SQL comment format
cqlComment = "--" + restOfLine
cqlStatement.ignore(cqlComment)



def parse_cql(cql, logging=True):
    tokens = []
    try:
        tokens = cqlStatement.parseString(cql)
        #tokens.pprint()

    except ParseException as ex:
        ex.explanation = '%s\n%s\n%s' % (cql, ' ' * ex.loc + '^\n', ex)
        if logging:
            log.error('\n%s', ex.explanation)
        raise

    return tokens
