# -*- coding: utf-8 -*-
# (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
import re
import types
import logging
import pyparsing
from copy import deepcopy
from lxml import etree
import unicodedata
from patzilla.access.sip.concordance import SipCountry, SipIpcClass, SipCpcClass
from patzilla.util.cql.pyparsing.parser import wildcards
from patzilla.util.cql.pyparsing.searchparser import SearchQueryParser
from patzilla.util.cql.pyparsing.serializer import trim_keywords
from patzilla.util.data.orderedset import OrderedSet
from patzilla.util.date import parse_date_within, iso_to_german, year_range_to_within
from patzilla.util.ipc.parser import IpcDecoder
from patzilla.util.python import _exception_traceback
from patzilla.util.xml.format import pretty_print, compact_print

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)


class SipExpression(object):

    modifier_defaults = {
        'fulltext': {
            'title': True,
            'abstract': True,
            'claim': True,
            'description': True,
            },
        }

    fulltext_field_modifier_map = {
        'ti': 'title',
        'ab': 'abstract',
        'cl': 'claim',
        'de': 'description',
        'bi': ['title', 'abstract', 'claim', 'description'],
        }
    fulltext_modifiers_off = {
        'title': 'false',
        'abstract': 'false',
        'claim': 'false',
        'description': 'false',
        }

    sip_xml_expression_templates = {
        'patentnumber': u'<patentnumber>{value}</patentnumber>',
        'fulltext':     u'<text searchintitle="{title}" searchinabstract="{abstract}" searchinclaim="{claim}" searchindescription="{description}" fullfamily="false">{value}</text>',
        #'applicant':    u'<applicant type="epo,inpadoc,original">{value}</applicant>',
        #'inventor':     u'<inventor type="epo,inpadoc,original">{value}</inventor>',
        'applicant':    u'<applicant type="epo,original">{value}</applicant>',
        'inventor':     u'<inventor type="epo,original">{value}</inventor>',
        'pubdate':      {
            'both':      u'<date type="publication" startdate="{startdate}" enddate="{enddate}" />',
            'startdate': u'<date type="publication" startdate="{startdate}" />',
            'enddate':   u'<date type="publication" enddate="{enddate}" />',
            }
    }

    xml_tag_fullfamily_capability = [

        'patentnumber',
        'text',
        'applicant',
        'inventor',

        'ipc', 'cpc',
        'country',
        'date',

    ]


    @classmethod
    def pair_to_sip_xml(cls, key, value, modifiers):

        # reformat modifiers to lower booleans
        # {u'fulltext': {u'claim': True, u'abstract': True, u'description': True, u'title': True}
        # ->
        # {u'fulltext': {u'claim': 'true', u'abstract': 'true', u'description': 'true', u'title': 'true'}
        for modifier_field, modifier_values in modifiers.iteritems():
            if type(modifiers[modifier_field]) is types.DictionaryType:
                for modifier_name, modifier_value in modifiers[modifier_field].iteritems():
                    modifiers[modifier_field][modifier_name] = str(modifier_value).lower()
            elif type(modifiers[modifier_field]) is types.BooleanType:
                modifiers[modifier_field] = str(modifiers[modifier_field]).lower()

        xml_part = None
        keywords = None

        if key == 'pubdate':

            try:

                if len(value) == 4 and value.isdigit():
                    # e.g. 1978
                    value = u'within {year}-01-01,{year}-12-31'.format(year=value)

                # e.g. 1990-2014, 1990 - 2014
                value = year_range_to_within(value)

                if 'within' in value:
                    try:
                        within_dates = parse_date_within(value)
                    except:
                        raise ValueError('Could not parse "within" expression')

                    if len(within_dates['startdate']) == 4 and within_dates['startdate'].isdigit():
                        within_dates['startdate'] = within_dates['startdate'] + '-01-01'
                    if len(within_dates['enddate']) == 4 and within_dates['enddate'].isdigit():
                        within_dates['enddate'] = within_dates['enddate'] + '-12-31'

                    if all(within_dates.values()):
                        template = cls.sip_xml_expression_templates[key]['both']
                    elif within_dates['startdate']:
                        template = cls.sip_xml_expression_templates[key]['startdate']
                    # API not capable of handling "enddate"-only attribute
                    #elif within_dates['enddate']:
                    #    template = cls.sip_xml_expression_templates[key]['enddate']
                    else:
                        raise ValueError('SIP cannot handle date ranges with end date only')

                    xml_part = template.format(
                        startdate=iso_to_german(within_dates['startdate']),
                        enddate=iso_to_german(within_dates['enddate']))

                else:
                    template = cls.sip_xml_expression_templates[key]['both']
                    xml_part = template.format(
                        startdate=iso_to_german(value),
                        enddate=iso_to_german(value))

            except Exception as ex:
                message = 'SIP query: Invalid date or range expression "{0}". Reason: {1}'.format(value, ex)
                logger.warn(message + ' Exception was: {0}'.format(_exception_traceback()))
                return {'error': True, 'message': message}


        elif key == 'country':

            if ' and ' in value.lower():
                message = 'SIP query: Concatenating offices with "AND" would yield zero results'
                logger.warn(message)
                return {'error': True, 'message': message}

            entries = re.split(' or ', value, flags=re.IGNORECASE)
            entries = [entry.strip() for entry in entries]
            ccids = []
            for country in entries:
                country = country.upper()
                sip_country = SipCountry.objects(cc=country).first()
                if sip_country:
                    sip_ccid = sip_country.ccid
                    ccids.append(sip_ccid)
                else:
                    message = 'SIP query: Country "{0}" could not be resolved'.format(country)
                    logger.warn(message)
                    return {'error': True, 'message': message}

            if ccids:
                xml_part = '<country>\n' + '\n'.join(['<ccid>{ccid}</ccid>'.format(ccid=ccid) for ccid in ccids]) + '\n</country>'


        elif key == 'class':

            try:
                expression = SipCqlClass(value)
                xml_part = expression.dumpxml()

                # debugging
                #print '-' * 42
                #print pretty_print(xml_part)

            except ClassDecodingError as ex:
                return {'error': True, 'message': str(ex)}

            except pyparsing.ParseException as ex:
                return {'error': True, 'message': '<pre>' + str(ex.explanation) + '</pre>'}


        elif key == 'fulltext':
            """
            parse cql subexpression (possible fields are ti, ab, de, cl, bi) and map to SIP syntax
            """

            try:
                expression = SipCqlFulltext(value, modifiers=modifiers.get(key, {}))
                xml_part = expression.dumpxml()
                keywords = expression.keywords()

                # debugging
                #print '-' * 42
                #print pretty_print(xml_part)

            except FulltextDecodingError as ex:
                return {'error': True, 'message': unicode(ex)}

            except pyparsing.ParseException as ex:
                return {'error': True, 'message': u'<pre>' + ex.explanation + '</pre>'}

            except SyntaxError as ex:
                return {'error': True, 'message': u'<pre>' + unicode(ex) + '</pre>'}

        elif key in cls.sip_xml_expression_templates:
            template = cls.sip_xml_expression_templates[key]

            if key == 'patentnumber':
                value = value.upper()

            xml_part = template.format(key=key, value=value.strip(), **modifiers.get(key, {}))

        else:
            logger.warn('SIP query: Could not handle pair {0}={1}'.format(key, value))


        response = {}
        if xml_part:
            response = {'query': xml_part}

        if keywords:
            response.update({'keywords': keywords})

        return response


    @classmethod
    def compute_modifiers(cls, modifiers):

        # prefer defaults (all True), but mixin modifiers from query
        for modifier_field, modifier_values in cls.modifier_defaults.iteritems():
            if modifier_field in cls.modifier_defaults:
                backup = deepcopy(modifiers.get(modifier_field, {}))
                modifiers[modifier_field] = cls.modifier_defaults[modifier_field]
                modifiers[modifier_field].update(backup)

        return modifiers

    @classmethod
    def enrich_fullfamily(cls, xml_query):

        # parse xml search expression
        parser = etree.XMLParser()
        root = etree.fromstring(xml_query, parser)

        # amend dom by adding fullfamily="true" attributes to appropriate elements
        for element_name in cls.xml_tag_fullfamily_capability:

            # handle root element
            if root.tag == element_name:
                root.attrib['fullfamily'] = 'true'

            # handle nested elements
            element_path = './/{}'.format(element_name)
            elements = root.findall(element_path)
            for element in elements:
                element.attrib['fullfamily'] = 'true'

        # serialize to xml text representation
        xml = etree.tostring(root)
        xml = xml.strip()
        return xml


class ClassDecodingError(Exception):
    pass

class FulltextDecodingError(Exception):
    pass


class SipCqlBase(object):

    def __init__(self, expression=None, modifiers=None):

        self.modifiers = modifiers or {}
        self.ast = None

        self.keyword_set = OrderedSet()
        self.parser = SearchQueryParser()

        if expression:
            self.loads(expression)

    def loads(self, expression):
        self.expression = expression
        self.ast = self.parse()

    def dumpxml(self, pretty=False):

        if self.ast is None:
            return ''

        # convert to proper xml representation
        xml = self.etree_to_xml(self.ast, pretty)

        return xml

    def keywords(self):
        return trim_keywords(self.keyword_set)

    def keyword_add(self, keyword):
        self.keyword_set.add(keyword)

    def to_etree(self, expression):

        # parse search expression
        try:
            result = self.parser._parser(expression, parseAll=True)

        except pyparsing.ParseException as ex:
            ex.explanation = u'%s\n%s\n%s' % (expression, u' ' * ex.loc + u'^\n', ex)
            logger.error(u'\n%s', ex.explanation)
            raise

        #print 'result:', result, type(result), dir(result)

        if type(result[0]) is pyparsing.ParseResults:
            result = result[0]

        result_xml = result.asXML()
        logger.debug('pyparsing xml:\n %s\n---------------------', result_xml)

        # amend result by manipulating its xml representation
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(result_xml, parser)

        return root

    def etree_to_xml(self, tree, pretty=False):
        xml = etree.tostring(tree)
        xml = xml.strip()
        if pretty:
            xml = pretty_print(xml)
        else:
            xml = compact_print(xml)
        return xml

    def strip_parenthesis(self, element):

        # decapsulate "parenthesis" nodes (strip "parenthesis" tags)
        for parenthesis in list(element.iter('parenthesis')):

            parent = parenthesis.getparent()
            #parent = element.getparent()
            #print 'parenthesis:', parenthesis.text, parent

            # move children one level up
            if parent is not None:
                for child in parenthesis:
                    parent.append(child)
                parent.remove(parenthesis)

            # when operating on root level, return first child
            else:
                return list(element)[0]

        return element


class SipCqlClass(SipCqlBase):

    def parse(self):

        # parse search expression
        root = self.to_etree(self.expression)

        # decapsulate and translate "word" and "ITEM" nodes
        for value_node in list(root.iter('value')):

            # decode and manipulate class value
            if value_node.text is None:
                continue
            expanded_xml = self.expand_class(value_node.text)

            # replace/mungle xml node(s)
            xml_node = etree.XML(expanded_xml)
            if value_node == root:
                root = xml_node
            else:
                parent_node = value_node.getparent()
                parent_node.replace(value_node, xml_node)


        # unqualified term fallback

        # when there's no qualifying fieldname (bi=, ti=, ab=, ...),
        # strip away superfluous <value>...</value> nesting
        if root.tag in ['value']:
            root = list(root)[0]


        # decapsulate "parenthesis" nodes (strip "parenthesis" tags)
        return self.strip_parenthesis(root)

    def expand_class(self, value):

        ipc_raw = value
        ipc_raw_stripped = ipc_raw.rstrip(wildcards + '/ .')

        # check for right truncated ipc classes
        right_truncation = False

        try:
            ipc = IpcDecoder(ipc_raw_stripped)
            if ipc.ipc['subgroup'] is None:
                ipc.ipc['subgroup'] = '00'
                right_truncation = True
            ipc_ops = ipc.formatOPS()
            self.keyword_add(ipc_ops)

        except:
            message = 'SIP query: Class "{0}" could not be decoded.'.format(ipc_raw_stripped)
            logger.warn(message)
            raise ClassDecodingError(message)


        if right_truncation:
            modifier = 'SmartSelect="true"'
        else:
            modifier = 'SmartSelect="false"'

        sip_ipc = SipIpcClass.objects(ipc=ipc_ops).first()
        sip_cpc = SipCpcClass.objects(cpc=ipc_ops).first()
        if not sip_ipc and not sip_cpc:
            message = 'SIP query: Class "{0}" could not be resolved.'.format(ipc_ops)
            logger.warn(message)
            raise ClassDecodingError(message)

        ipc_expression = None
        cpc_expression = None
        expression_entries = []

        if sip_ipc:

            ipc_expression =\
            '<ipc {0}>\n'.format(modifier) +\
            '<ipcid>{ipcid}</ipcid>'.format(ipcid=sip_ipc.itid) +\
            '\n</ipc>'
            expression_entries.append(ipc_expression)

        if sip_cpc:

            cpc_expression =\
            '<cpc {0}>\n'.format(modifier) +\
            '<cpcid>{cpcid}</cpcid>'.format(cpcid=sip_cpc.cpcid) +\
            '\n</cpc>'
            expression_entries.append(cpc_expression)

        if len(expression_entries) == 1:
            xml = expression_entries[0]

        elif len(expression_entries) > 1:

            # regular implementation
            xml = '<or>' + '\n'.join(expression_entries) + '</or>'

        return xml


class SipCqlFulltext(SipCqlBase):

    def parse(self):

        # apply asciifolding
        self.expression = strip_accents(self.expression)

        # parse search expression
        logger.debug('self.expression: %s', self.expression)
        root = self.to_etree(self.expression)
        logger.debug('term:\n%s', pretty_print(etree.tostring(root)))

        # HACK against corner case ab=(42)
        """
        <parenthesis>
            <index>ab</index>
            <binop>=</binop>
            <value>42</value>
        </parenthesis>
        """

        # rewrite element from "parenthesis" to "term" if structure looks like it
        def eexists(element, name):
            return element.find(name) is not None
        child_constraints =\
            all(map(lambda x: eexists(root, x), ['index', 'binop'])) and \
            any(map(lambda x: eexists(root, x), ['value', 'quotes']))
        if root.tag == 'parenthesis' and child_constraints:
            root.tag = 'term'

        # also rewrite all other parenthesis looking like terms
        for parens in root.iter('parenthesis'):
            child_constraints =\
                all(map(lambda x: eexists(parens, x), ['index', 'binop'])) and\
                any(map(lambda x: eexists(parens, x), ['value', 'quotes', 'or', 'and', 'not']))
            if child_constraints:
                parens.tag = 'term'

        logger.debug('before term:\n%s', pretty_print(etree.tostring(root)))

        # decapsulate and translate "term" nodes
        for term in list(root.iter('term')):

            # 1. decode and convert term structure
            index = term.find('index').text
            binop = term.find('binop').text

            # 1.a default value decoding
            #value = term.find('value').text
            # 1.b makes things like ab="42" possible
            # FIXME: catch IndexError, throw FulltextDecodingError
            value_quotes = term.xpath('value|quotes')
            boolean_content = term.xpath('and|or|not')

            if value_quotes:
                value = self.decode_quoted_value(value_quotes[0])
                self.keyword_add(value)

            elif boolean_content:
                value = self.convert_boolean_nodes(term)
                value = value.replace(u'and not', u'not')


            # 2. expand triple
            triple = index, binop, value
            expanded_xml = self.expand_fulltext(triple)


            # 3. replace term by computed representation
            xml_node = etree.XML(expanded_xml)

            # replace root node
            if term == root:
                root = xml_node

            # replace nested term
            else:
                parent_node = term.getparent()
                parent_node.replace(term, xml_node)

        logger.debug('after term:\n' + pretty_print(etree.tostring(root)))

        # decapsulate and translate "parenthesis" nodes
        for container in list(root.iter('parenthesis')):
            root = self.convert_elements(root, container, ['and', 'or', 'not'])
            root = self.convert_elements(root, container, ['near', 'span'])

        logger.debug('after parenthesis:\n' + pretty_print(etree.tostring(root)))

        # unqualified terms, i.e. when there's no qualifying fieldname (bi=, ti=, ab=, ...),

        # extrapolate field "bi=" (search in all fulltext fields)
        root = self.convert_elements(root, root, ['value', 'quotes'])
        root = self.convert_elements(root, root, ['near', 'span'])

        # decapsulate "parenthesis" nodes (strip "parenthesis" tags)
        root = self.strip_parenthesis(root)

        #print "current:\n", pretty_print(etree.tostring(root))

        # HACK to make unqualified expressions with boolean operators possible
        # apply only if tree does not contain already expanded <text ...> elements, otherwise things go haywire
        if root.tag in ['and', 'or', 'not'] and root.xpath('value') and not root.xpath('//text'):
            root = self.convert_elements(root, root, ['and', 'or', 'not'])

        # HACK to expand leftover <value></value> elements
        for value_element in list(root.iter('value')):
            index, binop = self._get_index_binop(value_element)
            triple = index, binop, value_element.text
            root = self.fulltext_to_xml_element(root, value_element, triple)

        return root

    def convert_elements(self, root, element, tags):

        if element.tag == 'parenthesis':
            element_nested = element.xpath('|'.join(tags))
            if element_nested:
                element_nested = element_nested[0]
            else:
                return root

        elif element.tag in tags:
            element = root
            element_nested = element

        else:
            return root


        #print 'element_nested:', element_nested
        tag = element_nested.tag
        if tag in ['value', 'and', 'or', 'not']:
            value = self.convert_boolean_nodes(element_nested)
            #print 'convert_boolean_nodes:', value
            # skip elements without a valid representation on this level, e.g. "(ab=fahrzeug or ab=pkw)"
            if not value:
                return root
            value = value.replace(u'and not', u'not')

        elif tag in ['near', 'span']:
            value = self.convert_proximity_nodes(element_nested)

        elif tag == 'quotes':
            value = self.decode_quoted_value(element_nested)
            self.keyword_add(value)

        index, binop = self._get_index_binop(element)
        triple = index, binop, value
        root = self.fulltext_to_xml_element(root, element, triple)

        return root


    def _get_index_binop(self, element):
        """
        # unqualified terms, i.e. when there's no qualifying fieldname (bi=, ti=, ab=, ...),
        # extrapolate field "bi=" (search in all fulltext fields)
        """
        index_node = element.find('index')
        binop_node = element.find('binop')

        # 1. index
        if index_node is not None:
            index = index_node.text
        else:
            index = u'bi'

        # 2. binop
        if binop_node is not None:
            binop = binop_node.text
        else:
            binop = u'='

        return index, binop


    def fulltext_to_xml_element(self, root, element, triple):

        # HACK for expressions without any field name qualifiers: pass-through 1:1 honoring modifiers from query
        # e.g. "vorgang" vs. "ab=vorgang"
        if '=' not in self.expression:
            expanded_xml = self.expand_fulltext(triple, modifiers=self.modifiers)
        else:
            expanded_xml = self.expand_fulltext(triple)

        xml_node = etree.XML(expanded_xml)

        parent = element.getparent()
        if parent is not None:
            parent.replace(element, xml_node)
        else:
            root = xml_node

        return root

    def convert_proximity_nodes(self, container):

        distance = container.xpath('distance')

        value = container.xpath('value')
        text = container.xpath('text')

        # fall back to using already translated "text" nodes
        if value:
            expression = map(lambda x: x.text, value)
            map(lambda x: self.keyword_add(x), expression)
        elif text:
            expression = map(lambda x: '({0})'.format(x.text), text)

        expression = u' '.join(expression)
        distance = distance[0].text
        value = u'{operator}({expression}, {distance})'.format(operator=container.tag, expression=expression, distance=distance)
        return value

    def convert_boolean_nodes(self, node):
        child_values = []
        for element in node:
            if element.tag in ['or', 'and', 'not']:
                child_values.append(self.convert_boolean_nodes(element))

            elif element.tag in ['value', 'quotes']:
                value = self.decode_quoted_value(element)
                if value:
                    child_values.append(value)
                    #print 'keyword:', value
                    self.keyword_add(value)

            elif element.tag == 'parenthesis':
                result = self.convert_boolean_nodes(element)
                if result:
                    result = u'(' + result + u')'
                child_values.append(result)

            elif element.tag in ['near', 'span']:
                child_values.append(self.convert_proximity_nodes(element))

            else:
                #msg = 'Encountered unknown tag "{0}" in "convert_boolean_nodes"'.format(element.tag)
                #logger.warn(msg)
                #print msg
                pass

        if len(child_values) == 1 and node.tag == 'not':
            child_values = [u'not ' + child_values[0]]

        return u' {0} '.format(node.tag).join(child_values)

    def decode_quoted_value(self, element):
        """
        Decodes xml like

        - <value>foo</value>
        - <quotes>
              <value>foo</value>
          </quotes>
        - <quotes>
              <value>foo</value>
              <value>bar</value>
              <value>baz</value>
          </quotes>

        """
        value = None

        if element.tag == 'value':
            value = element.text

        elif element.tag == 'quotes':
            values = map(lambda x: x.text, element.iter('value'))
            value = u'"{0}"'.format(u' '.join(values))

        return value

    def expand_fulltext(self, value, origin=None, modifiers=None):
        triple = value

        origin = origin or u'{0}{1}{2}'.format(*triple)

        ft_field, ft_op, ft_value = triple

        # use modifiers from request
        if modifiers:
            ft_modifiers = modifiers

        # compute modifiers from expression
        else:
            ft_field = ft_field.lower()
            try:
                ft_modifier = SipExpression.fulltext_field_modifier_map[ft_field]
            except KeyError:
                message = u'SIP expression "{0}" contains unknown index "{1}".'.format(origin, ft_field)
                logger.warn(message)
                raise FulltextDecodingError(message)

            ft_modifiers = SipExpression.fulltext_modifiers_off.copy()

            if type(ft_modifier) in types.StringTypes:
                ft_modifiers.update({ft_modifier: 'true'})
            elif type(ft_modifier) is types.ListType:
                for ft_mod_item in ft_modifier:
                    ft_modifiers.update({ft_mod_item: 'true'})

        template = SipExpression.sip_xml_expression_templates['fulltext']
        xml = template.format(key=ft_field, value=ft_value.strip(), **ft_modifiers)
        return xml


def strip_accents(s):
    # asciifolding
    # https://stackoverflow.com/questions/1410308/how-to-implement-unicode-string-matching-by-folding-in-python/1410365#1410365
    #return ''.join((c for c in unicodedata.normalize('NFD', unicode(s)) if unicodedata.category(c) != 'Mn'))
    result = []
    for char in s:
        if char.lower() in u'äöüß':
            result.append(char)
        else:
            char_decomposed = unicodedata.normalize('NFD', unicode(char))
            for cd in char_decomposed:
                if unicodedata.category(cd) != 'Mn':
                    result.append(cd)

    return ''.join(result)
