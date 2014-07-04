# -*- coding: utf-8 -*-
"""
Cheshire3 CQL Parser Implementation.

Author:  Rob Sanderson (azaroth@liv.ac.uk)
Version: 2.0    (CQL 1.2)
With thanks to Adam Dickmeiss and Mike Taylor for their valuable input.

Source:  https://github.com/cheshire3/cheshire3/blob/develop/cheshire3/cqlParser.py
License: Proprietary (Cheshire3 License)
         https://github.com/cheshire3/cheshire3/blob/develop/LICENSE.rst

See also: https://github.com/asl2/PyZ3950/blob/master/apache/CQLParser.py (v1.2)
          https://github.com/asl2/PyZ3950/blob/master/PyZ3950/CQLParser.py (v1.7)
License: Distributed and Usable under the GPL
"""

import types

from shlex import shlex
from xml.sax.saxutils import escape
from StringIO import StringIO
from __builtin__ import isinstance

serverChoiceRelation = "="
serverChoiceIndex = "cql.serverchoice"

order = ['=', '>', '>=', '<', '<=', '<>']
modifierSeparator = "/"
booleans = ['and', 'or', 'not', 'prox']
sortWord = 'sortby'

reservedPrefixes = {"srw": "http://www.loc.gov/zing/cql/srw-indexes/v1.0/",
                    "cql": "info:srw/cql-context-set/1/cql-v1.2"}

XCQLNamespace = "http://www.loc.gov/zing/cql/xcql/"

errorOnEmptyTerm = False          # index = ""
errorOnQuotedIdentifier = False   # "/foo/bar" = ""
errorOnDuplicatePrefix = False    # >a=b >a=c ""
fullResultSetNameCheck = True     # cql.rsn=a and cql.rsn=a    (mutant!)

# End of 'configurable' stuff


class Diagnostic(Exception):
    code = 10         # default to generic broken query diagnostic
    uri = "info:srw/diagnostic/1/"
    message = ""
    details = ""

    def __str__(self):
        return "{0.uri} [{0.message}]: {0.details}".format(self)
        #return "%s [%s]: %s" % (self.uri, self.message, self.details)

    def __init__(self, code=10, message="Malformed Query", details=""):
        self.uri = "info:srw/diagnostic/1/{0}".format(code)
        self.code = code
        self.message = message
        self.details = details
        Exception.__init__(self)


class PrefixableObject:
    "Root object for triple and searchClause"
    prefixes = {}
    parent = None
    config = None

    def __init__(self):
        self.prefixes = {}
        self.parent = None
        self.config = None

    def toXCQL(self, depth=0):
        space = "  " * depth
        xml = ['{s}<prefixes>\n']
        for p in self.prefixes.keys():
            xml.extend(["{s}  <prefix>\n",
                        "{s}    <name>{name}</name>\n",
                        "{s}    <identifier>{ident}</identifier>\n",
                        "{s}  </prefix>\n"])
        xml.append("{s}</prefixes>\n")
        return ''.join(xml).format(s=space, name=escape(p),
                                   ident=escape(self.prefixes[p]))

    def addPrefix(self, name, identifier):
        if (
            errorOnDuplicatePrefix and
            (name in self.prefixes or name in reservedPrefixes)
        ):
            # Maybe error
            diag = Diagnostic()
            diag.code = 45
            diag.details = name
            raise diag
        self.prefixes[name] = identifier

    def resolvePrefix(self, name):
        # Climb tree
        if name in reservedPrefixes:
            return reservedPrefixes[name]
        elif name in self.prefixes:
            return self.prefixes[name]
        elif self.parent is not None:
            return self.parent.resolvePrefix(name)
        elif self.config is not None:
            # Config is some sort of server config which specifies defaults
            return self.config.resolvePrefix(name)
        else:
            # Top of tree, no config, no resolution->Unknown indexset
            # For client we need to allow no prefix?
            #diag = Diagnostic15()
            #diag.details = name
            #raise diag
            return None


class PrefixedObject:
    "Root object for index, relation, relationModifier"
    prefix = ""
    prefixURI = ""
    value = ""
    parent = None

    def __init__(self, val):
        # All prefixed things are case insensitive
        self.origValue = val
        val = val.lower()
        if val and val[0] == '"' and val[-1] == '"':
            if errorOnQuotedIdentifier:
                diag = Diagnostic()
                diag.code = 14
                diag.details = val
                raise diag
            else:
                val = val[1:-1]
        self.value = val
        self.splitValue()

    def __str__(self):
        if (self.prefix):
            return "%s.%s" % (self.prefix, self.value)
        else:
            return self.value

    def splitValue(self):
        f = self.value.find(".")
        if (self.value.count('.') > 1):
            diag = Diagnostic()
            diag.code = 15
            diag.details = "Multiple '.' characters: %s" % (self.value)
            raise(diag)
        elif (f == 0):
            diag = Diagnostic()
            diag.code = 15
            diag.details = "Null indexset: %s" % (irt.index)
            raise(diag)
        elif f >= 0:
            self.prefix = self.value[:f].lower()
            self.value = self.value[f + 1:].lower()

    def resolvePrefix(self):
        if (not self.prefixURI):
            self.prefixURI = self.parent.resolvePrefix(self.prefix)
        return self.prefixURI


class ModifiableObject:
    # Treat modifiers as keys on boolean/relation?
    modifiers = []

    def __getitem__(self, k):
        if isinstance(k, int):
            try:
                return self.modifiers[k]
            except:
                return None
        for m in self.modifiers:
            if (str(m.type) == k or m.type.value == k):
                return m
        return None


class Triple (PrefixableObject):
    "Object to represent a CQL triple"
    leftOperand = None
    boolean = None
    rightOperand = None
    sortKeys = []

    def toXCQL(self, depth=0):
        "Create the XCQL representation of the object"
        space = "  " * depth
        if (depth == 0):
            xml = ['<triple xmlns="%s">\n' % (XCQLNamespace)]
        else:
            xml = ['%s<triple>\n' % (space)]

        if self.prefixes:
            xml.append(PrefixableObject.toXCQL(self, depth + 1))

        xml.append(self.boolean.toXCQL(depth + 1))
        xml.append("%s  <leftOperand>\n" % (space))
        xml.append(self.leftOperand.toXCQL(depth + 2))
        xml.append("%s  </leftOperand>\n" % (space))
        xml.append("%s  <rightOperand>\n" % (space))
        xml.append(self.rightOperand.toXCQL(depth + 2))
        xml.append("%s  </rightOperand>\n" % (space))

        if self.sortKeys:
            xml.append("  %s<sortKeys>\n" % space)
            for key in self.sortKeys:
                xml.append(key.toXCQL(depth + 2))
            xml.append("  %s</sortKeys>\n" % space)

        xml.append("%s</triple>\n" % (space))
        return ''.join(xml)

    def toCQL(self):
        txt = []
        if (self.prefixes):
            ptxt = []
            for p in self.prefixes.keys():
                if p != '':
                    ptxt.append('>%s="%s"' % (p, self.prefixes[p]))
                else:
                    ptxt.append('>"%s"' % (self.prefixes[p]))
            prefs = ' '.join(ptxt)
            txt.append(prefs)
        txt.append(self.leftOperand.toCQL())
        txt.append(self.boolean.toCQL())
        txt.append(self.rightOperand.toCQL())
        # Add sortKeys
        if self.sortKeys:
            txt.append("sortBy")
            for sk in self.sortKeys:
                txt.append(sk.toCQL())
        return u"({0})".format(u" ".join(txt))

    def getResultSetId(self, top=None):
        if (
            fullResultSetNameCheck == 0 or
            self.boolean.value in ['not', 'prox']
        ):
            return ""

        if top is None:
            topLevel = 1
            top = self
        else:
            topLevel = 0

        # Iterate over operands and build a list
        rsList = []
        if isinstance(self.leftOperand, Triple):
            rsList.extend(self.leftOperand.getResultSetId(top))
        else:
            rsList.append(self.leftOperand.getResultSetId(top))
        if isinstance(self.rightOperand, Triple):
            rsList.extend(self.rightOperand.getResultSetId(top))
        else:
            rsList.append(self.rightOperand.getResultSetId(top))

        if topLevel == 1:
            # Check all elements are the same
            # if so we're a fubar form of present
            if (len(rsList) == rsList.count(rsList[0])):
                return rsList[0]
            else:
                return ""
        else:
            return rsList


class SearchClause (PrefixableObject):
    "Object to represent a CQL searchClause"
    index = None
    relation = None
    term = None
    sortKeys = []

    def __init__(self, ind, rel, t):
        PrefixableObject.__init__(self)
        self.index = ind
        self.relation = rel
        self.term = t
        ind.parent = self
        rel.parent = self
        t.parent = self

    def toXCQL(self, depth=0):
        "Produce XCQL version of the object"
        space = "  " * depth
        if (depth == 0):
            xml = ['<searchClause xmlns="%s">\n' % (XCQLNamespace)]
        else:
            xml = ['%s<searchClause>\n' % (space)]

        if self.prefixes:
            xml.append(PrefixableObject.toXCQL(self, depth + 1))

        xml.append(self.index.toXCQL(depth + 1))
        xml.append(self.relation.toXCQL(depth + 1))
        xml.append(self.term.toXCQL(depth + 1))

        if self.sortKeys:
            xml.append("  %s<sortKeys>\n" % space)
            for key in self.sortKeys:
                xml.append(key.toXCQL(depth + 2))
            xml.append("  %s</sortKeys>\n" % space)

        xml.append("%s</searchClause>\n" % (space))
        return ''.join(xml)

    def toCQL(self):
        text = []
        for p in self.prefixes.keys():
            if p != '':
                text.append('>%s="%s"' % (p, self.prefixes[p]))
            else:
                text.append('>"%s"' % (self.prefixes[p]))
        text.append('%s %s "%s"' % (self.index,
                                    self.relation.toCQL(),
                                    self.term.toCQL()))
        # Add sortKeys
        if self.sortKeys:
            text.append("sortBy")
            for sk in self.sortKeys:
                text.append(sk.toCQL())
        return ' '.join(text)

    def getResultSetId(self, top=None):
        idx = self.index
        idx.resolvePrefix()
        if (
            idx.prefixURI == reservedPrefixes['cql'] and
            idx.value.lower() == 'resultsetid'
        ):
            return self.term.value
        else:
            return ""


class Index(PrefixedObject, ModifiableObject):
    "Object to represent a CQL index"

    def __init__(self, val):
        PrefixedObject.__init__(self, val)
        if self.value in ['(', ')'] + order:
            diag = Diagnostic()
            diag.message = "Invalid characters in index name"
            diag.details = self.value
            raise diag

    def toXCQL(self, depth=0):
        space = "  " * depth
        if (depth == 0):
            ns = ' xmlns="%s"' % (XCQLNamespace)
        else:
            ns = ""
        xml = ["%s<index%s>\n" % (space, ns),
               "  %s<value>%s</value>\n" % (space, escape(str(self)))]
        if self.modifiers:
            xml.append("%s  <modifiers>\n" % (space))
            for m in self.modifiers:
                xml.append(m.toXCQL(depth + 2))
            xml.append("%s  </modifiers>\n" % (space))
        xml.append("%s</index>\n" % space)
        return ''.join(xml)

    def toCQL(self):
        txt = [str(self)]
        for m in self.modifiers:
            txt.append(m.toCQL())
        return '/'.join(txt)


class Relation(PrefixedObject, ModifiableObject):
    "Object to represent a CQL relation"
    def __init__(self, rel, mods=[]):
        self.prefix = "cql"
        PrefixedObject.__init__(self, rel)
        self.modifiers = mods
        for m in mods:
            m.parent = self

    def toXCQL(self, depth=0):
        "Create XCQL representation of object"
        if (depth == 0):
            ns = ' xmlns="%s"' % (XCQLNamespace)
        else:
            ns = ""

        space = "  " * depth

        xml = ["%s<relation%s>\n" % (space, ns)]
        xml.append("%s  <value>%s</value>\n" % (space, escape(self.value)))
        if self.modifiers:
            xml.append("%s  <modifiers>\n" % (space))
            for m in self.modifiers:
                xml.append(m.toXCQL(depth + 2))
            xml.append("%s  </modifiers>\n" % (space))
        xml.append("%s</relation>\n" % (space))
        return ''.join(xml)

    def toCQL(self):
        txt = [self.value]
        txt.extend(map(str, self.modifiers))
        return '/'.join(txt)


class Term:

    value = ""

    def __init__(self, v):
        if (v != ""):
            # Unquoted literal
            if v in ['>=', '<=', '>', '<', '<>', "/", '=']:
                diag = Diagnostic()
                diag.code = 25
                diag.details = self.value
                raise diag

            # Check existence of meaningful term
            nonanchor = 0
            for c in v:
                if c != "^":
                    nonanchor = 1
                    break
            if not nonanchor:
                diag = Diagnostic()
                diag.code = 32
                diag.details = "Only anchoring charater(s) in term: " + v
                raise diag

            # Unescape quotes
            if (v[0] == '"' and v[-1] == '"'):
                v = v[1:-1]
            v = v.replace('\\"', '"')

            # Check for badly placed \s
            startidx = 0
            idx = v.find("\\", startidx)
            while (idx > -1):
                if len(v) < idx + 2 or not v[idx + 1] in ['?', '\\', '*', '^']:
                    diag = Diagnostic()
                    diag.code = 26
                    diag.details = v
                    raise diag
                if v[idx + 1] == '\\':
                    startidx = idx + 2
                else:
                    startidx = idx + 1
                idx = v.find("\\", startidx)
        elif errorOnEmptyTerm:
            diag = Diagnostic()
            diag.code = 27
            raise diag
        self.value = v

    def __str__(self):
        return self.value

    def toXCQL(self, depth=0):
        if (depth == 0):
            ns = ' xmlns="%s"' % (XCQLNamespace)
        else:
            ns = ""
        return "%s<term%s>%s</term>\n" % ("  " * depth, ns, escape(self.value))

    def toCQL(self):
        return self.value.replace('"', '\\"')


class Boolean(ModifiableObject):
    "Object to represent a CQL boolean"

    value = ""
    parent = None

    def __init__(self, bool, mods=[]):
        self.value = bool
        self.modifiers = mods
        self.parent = None

    def toXCQL(self, depth=0):
        "Create XCQL representation of object"
        space = "  " * depth
        xml = ["%s<boolean>\n" % (space)]
        xml.append("%s  <value>%s</value>\n" % (space, escape(self.value)))
        if self.modifiers:
            xml.append("%s  <modifiers>\n" % (space))
            for m in self.modifiers:
                xml.append(m.toXCQL(depth + 2))
            xml.append("%s  </modifiers>\n" % (space))
        xml.append("%s</boolean>\n" % (space))
        return ''.join(xml)

    def toCQL(self):
        txt = [self.value]
        for m in self.modifiers:
            txt.append(m.toCQL())
        return '/'.join(txt)

    def resolvePrefix(self, name):
        return self.parent.resolvePrefix(name)


class ModifierType(PrefixedObject):
    # Same as index, but we'll XCQLify in ModifierClause
    parent = None
    prefix = "cql"


class ModifierClause:
    "Object to represent a relation modifier"
    parent = None
    type = None
    comparison = ""
    value = ""

    def __init__(self, type, comp="", val=""):
        self.type = ModifierType(type)
        self.type.parent = self
        self.comparison = comp
        self.value = val

    def __str__(self):
        if (self.value):
            return "%s%s%s" % (str(self.type), self.comparison, self.value)
        else:
            return "%s" % (str(self.type))

    def toXCQL(self, depth=0):
        if (self.value):
            return '\n'.join(["%s<modifier>" % ("  " * depth),
                              "%s<type>%s</type>" %
                              ("  " * (depth + 1), escape(str(self.type))),
                              "%s<comparison>%s</comparison>" %
                              ("  " * (depth + 1), escape(self.comparison)),
                              "%s<value>%s</value>" %
                              ("  " * (depth + 1), escape(self.value)),
                              "%s</modifier>" % ("  " * depth)
                              ])
        else:
            return '\n'.join(["%s<modifier>" % ("  " * depth),
                              "             %s<type>%s</type>" %
                              ("  " * (depth + 1), escape(str(self.type))),
                              "%s</modifier>" % ("  " * depth)
                              ])

    def toCQL(self):
        return str(self)

    def resolvePrefix(self, name):
        # Need to skip parent, which has its own resolvePrefix
        # eg boolean or relation, neither of which is prefixable
        return self.parent.parent.resolvePrefix(name)


# Requires changes for:  <= >= <>, and escaped \" in "
# From shlex.py (std library for 2.2+)
class CQLshlex(shlex):
    "shlex with additions for CQL parsing"
    quotes = '"'
    commenters = ""
    nextToken = ""

    def __init__(self, thing):
        shlex.__init__(self, thing)
        self.wordchars += "!@#$%^&*-+{}[];,.?|~`:\\"
        # self.wordchars += ''.join(map(chr, range(128,254)))
        self.wordchars = self.wordchars.decode('utf-8')

    def read_token(self):
        "Read a token from the input stream (no pushback or inclusions)"

        while 1:
            if (self.nextToken != ""):
                self.token = self.nextToken
                self.nextToken = ""
                # Bah. SUPER ugly non portable
                if self.token == "/":
                    self.state = ' '
                    break

            nextchar = self.instream.read(1)
            if nextchar == '\n':
                self.lineno = self.lineno + 1

            if self.state is None:
                self.token = ''        # past end of file
                break
            elif self.state == ' ':
                if not nextchar:
                    self.state = None  # end of file
                    break
                elif nextchar in self.whitespace:
                    if self.token:
                        break   # emit current token
                    else:
                        continue
                elif nextchar in self.commenters:
                    self.instream.readline()
                    self.lineno = self.lineno + 1
                elif nextchar in self.wordchars:
                    self.token = nextchar
                    self.state = 'a'
                elif nextchar in self.quotes:
                    self.token = nextchar
                    self.state = nextchar
                elif nextchar in ['<', '>']:
                    self.token = nextchar
                    self.state = '<'
                else:
                    self.token = nextchar
                    if self.token:
                        break   # emit current token
                    else:
                        continue
            elif self.state == '<':
                # Only accumulate <=, >= or <>
                if self.token == ">" and nextchar == "=":
                    self.token = self.token + nextchar
                    self.state = ' '
                    break
                elif self.token == "<" and nextchar in ['>', '=']:
                    self.token = self.token + nextchar
                    self.state = ' '
                    break
                elif not nextchar:
                    self.state = None
                    break
                elif nextchar == "/":
                    self.state = "/"
                    self.nextToken = "/"
                    break
                elif nextchar in self.wordchars:
                    self.state = 'a'
                    self.nextToken = nextchar
                    break
                elif nextchar in self.quotes:
                    self.state = nextchar
                    self.nextToken = nextchar
                    break
                else:
                    self.state = ' '
                    break

            elif self.state in self.quotes:
                self.token = self.token + nextchar
                # Allow escaped quotes
                if nextchar == self.state and self.token[-2] != '\\':
                    self.state = ' '
                    break
                elif not nextchar:      # end of file
                    # Override SHLEX's ValueError to throw diagnostic
                    diag = Diagnostic()
                    diag.details = self.token[:-1]
                    raise diag
            elif self.state == 'a':
                if not nextchar:
                    self.state = None   # end of file
                    break
                elif nextchar in self.whitespace:
                    self.state = ' '
                    if self.token:
                        break   # emit current token
                    else:
                        continue
                elif nextchar in self.commenters:
                    self.instream.readline()
                    self.lineno = self.lineno + 1
                elif (ord(nextchar) > 126 or
                      nextchar in self.wordchars or
                      nextchar in self.quotes):
                    self.token = self.token + nextchar
                elif nextchar in ['>', '<']:
                    self.nextToken = nextchar
                    self.state = '<'
                    break
                else:
                    self.push_token(nextchar)
                    # self.pushback = [nextchar] + self.pushback
                    self.state = ' '
                    if self.token:
                        break   # emit current token
                    else:
                        continue
        result = self.token
        self.token = ''
        return result


class CQLParser:
    "Token parser to create object structure for CQL"
    parser = ""
    currentToken = ""
    nextToken = ""

    def __init__(self, p):
        """ Initialise with shlex parser """
        self.parser = p
        self.fetch_token()  # Fetches to next
        self.fetch_token()  # Fetches to curr

    def is_sort(self, token):
        return token.lower() == sortWord

    def is_boolean(self, token):
        "Is the token a boolean"
        token = token.lower()
        return token in booleans

    def fetch_token(self):
        """ Read ahead one token """
        self.currentToken = self.nextToken
        self.nextToken = self.parser.get_token()

    def prefixes(self):
        "Create prefixes dictionary"
        prefs = {}
        while (self.currentToken == ">"):
            # Strip off maps
            self.fetch_token()
            identifier = []
            if self.nextToken == "=":
                # Named map
                name = self.currentToken
                self.fetch_token()  # = is current
                self.fetch_token()  # id is current
                identifier.append(self.currentToken)
            else:
                name = ""
                identifier.append(self.currentToken)
            self.fetch_token()
            # URIs can have slashes, and may be unquoted (standard BNF checked)
            while self.currentToken == '/' or identifier.endswith('/'):
                identifier.append(self.currentToken)
                self.fetch_token()
            identifier = ''.join(identifier)
            if (
                len(identifier) > 1 and
                identifier[0] == '"' and
                identifier.endswith('"')
            ):
                identifier = identifier[1:-1]
            prefs[name.lower()] = identifier
        return prefs

    def query(self):
        """ Parse query """
        prefs = self.prefixes()
        left = self.subQuery()
        while 1:
            if not self.currentToken:
                break
            if self.is_boolean(self.currentToken):
                boolobject = self.boolean()
                right = self.subQuery()
                trip = tripleType()
                # Setup objects
                trip.leftOperand = left
                trip.boolean = boolobject
                trip.rightOperand = right
                left.parent = trip
                right.parent = trip
                boolobject.parent = trip
                left = trip
            elif self.is_sort(self.currentToken):
                # consume and parse with modified sort spec
                left.sortKeys = self.sortQuery()
            else:
                break
        for p in prefs.keys():
            left.addPrefix(p, prefs[p])
        return left

    def sortQuery(self):
        # current is 'sort' reserved word
        self.fetch_token()
        keys = []
        if not self.currentToken:
            # trailing sort with no keys
            diag = Diagnostic()
            diag.message = "No sort keys supplied"
            raise diag
        while self.currentToken:
            # current is index name
            if self.currentToken == ')':
                break
            index = indexType(self.currentToken)
            self.fetch_token()
            index.modifiers = self.modifiers()
            keys.append(index)
        return keys

    def subQuery(self):
        """ Find either query or clause """
        if self.currentToken == "(":
            self.fetch_token()  # Skip (
            object = self.query()
            if self.currentToken == ")":
                self.fetch_token()  # Skip )
            else:
                diag = Diagnostic()
                diag.details = self.currentToken
                raise diag
        else:
            prefs = self.prefixes()
            if (prefs):
                object = self.query()
                for p in prefs.keys():
                    object.addPrefix(p, prefs[p])
            else:
                object = self.clause()
        return object

    def clause(self):
        """ Find searchClause """
        bool = self.is_boolean(self.nextToken)
        sort = self.is_sort(self.nextToken)
        if not sort and not bool and not (self.nextToken in [')', '(', '']):
            index = indexType(self.currentToken)
            self.fetch_token()   # Skip Index
            rel = self.relation()
            if (self.currentToken == ''):
                diag = Diagnostic()
                diag.details = "Expected Term, got end of query."
                raise(diag)

            self.before_clause()
            term = termType(self.currentToken)
            self.fetch_token()   # Skip Term
            irt = searchClauseType(index, rel, term)
            self.after_clause(irt)

        elif (self.currentToken and
              (bool or sort or self.nextToken in [')', ''])):
            irt = searchClauseType(indexType(serverChoiceIndex),
                                   relationType(serverChoiceRelation),
                                   termType(self.currentToken))
            self.fetch_token()

        elif self.currentToken == ">":
            prefs = self.prefixes()
            object = self.clause()
            for p in prefs.keys():
                object.addPrefix(p, prefs[p])
            return object

        else:
            diag = Diagnostic()
            diag.details = ("Expected Boolean or Relation but got: " +
                            self.currentToken)
            raise diag
        return irt

    def before_clause(self):
        pass

    def after_clause(self, irt):
        pass

    def modifiers(self):
        mods = []
        while (self.currentToken == modifierSeparator):
            self.fetch_token()
            mod = self.currentToken
            mod = mod.lower()
            if (mod == modifierSeparator):
                diag = Diagnostic()
                diag.details = "Null modifier"
                raise diag
            self.fetch_token()
            comp = self.currentToken
            if (comp in order):
                self.fetch_token()
                value = self.currentToken
                self.fetch_token()
            else:
                comp = ""
                value = ""
            mods.append(ModifierClause(mod, comp, value))
        return mods

    def boolean(self):
        """ Find boolean """
        self.currentToken = self.currentToken.lower()
        if self.currentToken in booleans:
            bool = booleanType(self.currentToken)
            self.fetch_token()
            bool.modifiers = self.modifiers()
            for b in bool.modifiers:
                b.parent = bool
        else:
            diag = Diagnostic()
            diag.details = self.currentToken
            raise diag
        return bool

    def relation(self):
        """ Find relation """
        self.currentToken = self.currentToken.lower()
        rel = relationType(self.currentToken)
        self.fetch_token()
        rel.modifiers = self.modifiers()
        for r in rel.modifiers:
            r.parent = rel
        return rel


def parse(query):
    """Return a searchClause/triple object from CQL string"""

    if type(query) == str:
        try:
            query = query.decode("utf-8")
        except Exception, e:
            raise

    q = StringIO(query)
    lexer = CQLshlex(q)
    parser = CQLParser(lexer)
    object = parser.query()
    if parser.currentToken != '':
        diag = Diagnostic()
        diag.code = 10
        diag.details = ("Unprocessed tokens remain: " +
                        repr(parser.currentToken))
        raise diag
    else:
        del lexer
        del parser
        del q
        return object


# Assign our objects to generate
tripleType = Triple
booleanType = Boolean
relationType = Relation
searchClauseType = SearchClause
modifierClauseType = ModifierClause
modifierTypeType = ModifierType
indexType = Index
termType = Term
