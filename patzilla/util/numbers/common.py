# -*- coding: utf-8 -*-
# (c) 2007,2014-2017 Andreas Motl <andreas.motl@elmyra.de>
import re
import types
import logging
from patzilla.util.data.container import SmartBunch
from patzilla.util.numbers.helper import strip_spaces

"""
Common lowlevel functions
"""

log = logging.getLogger(__name__)


class DocumentIdentifierBunch(SmartBunch):

    def __str__(self):
        return self.dump()

    def serialize(self):
        return join_patent(self)


def join_patent(patent):
    if not patent:
        return
    number = patent['country'] + patent['number'] + patent.get('kind', '')
    return number

def decode_patent_number(patent):
    if isinstance(patent, types.StringTypes):
        decoded = split_patent_number(patent)
    elif isinstance(patent, types.DictionaryType):
        decoded = patent
    else:
        raise TypeError(u'Document number "{patent}" of type "{type}" could not be decoded'.format(patent=patent, type=type(patent)))
    return decoded

def split_patent_number(patent_number):

    if not patent_number:
        return

    # set common pattern for splitting patent number into segments

    # pattern evolution
    # e.g. DE12345A1
    #pattern = '^(\D\D)(\d+?)(\D.?)?(_.+)?$'
    # e.g. USPP12009P2
    #pattern = '^(\D\D)(\D{,2}\d+?)(\D.?)?(_.+)?$'
    # e.g. US0PP12009P2
    #pattern = '^(\D\D)(0?\D{,2}\d+?)(\D.?)?(_.+)?$'
    # e.g. DE10001499.2
    #pattern = '^(\D\D)(0?\D{,2}[\d.]+?)([a-zA-Z].?)?(_.+)?$'

    # e.g. BR000PI0507004A, MX00PA05006297A, ITVR0020130124A
    pattern = '^(\D\D)(0*\D{,2}[\d.]+?)([a-zA-Z].?)?(_.+)?$'



    # remove leading and trailing space characters
    patent_number = patent_number.strip()

    # pre-flight check for WO applications (let them pass through)

    if patent_number.startswith('WOPCT'):
        patent = {
            'country': 'WO',
            'number': patent_number[2:],
            'kind': '',
            'ext': '',
            }
        return patent

    elif patent_number.startswith('PCT'):
        patent = {
            'country': 'WO',
            'number': patent_number,
            'kind': '',
            'ext': '',
            }
        return patent

    elif patent_number.startswith('AT') and '/' in patent_number:
        patent_number = strip_spaces(patent_number)
        pattern = '^(\D\D)([\d|\/]+?)(\D.?)?(_.+)?$'

    elif patent_number.startswith('JP'):
        """
        Japanese numbers do have "Japanese imperial years vs. Western years":
        - SHOWA  (SHO, S)
        - HEISEI (HEI, H)

        See also: http://www.epo.org/searching/asian/japan/numbering.html
        """
        # JPS5647318A, JP00000S602468B2
        #pattern = '^(\D\D)([SH\d|-]+?)(\D.?)?(_.+)?$'

        # JPWO2013186910A1
        pattern = '^(\D\D)((?:WO)?[SH\d|-]+?)(\D.?)?(_.+)?$'

    elif patent_number.startswith('IN'):
        """
        examples:
        IN2011MU02282A, IN2009KN02715A, IND265197S
        """
        pattern = '^(\D\D)(D?\d+\D*?\d+)(\D.?)?(_.+)?$'

    else:
        patent_number = modify_invalid_patent_number(patent_number)


    # actually split combined patent number into segments
    r = re.compile(pattern)
    m = r.match(patent_number)
    if m:
        matchnames = ['country', 'number', 'kind', 'ext']

        """
        # statically create parts-hash from matches
        parts = {
          'country': str(m.group(1)),
          'number':  str(m.group(2)),
          'kind':    str(m.group(3)),
          'ext':     str(m.group(4)),
        }
        """

        # dynamically create parts-hash checking whether matches are valid or not
        parts = {}
        for i in range(0, len(matchnames)):
            name = matchnames[i]
            value = ''
            if m.group(i+1):
                value = m.group(i+1)
            parts[name] = value

        split_patent_number_more(parts)

        dib = DocumentIdentifierBunch(parts)
        return dib

    else:
        log.error(u'Could not parse patent number "{0}"'.format(patent_number))


def split_patent_number_more(patent):
    # filter: special document handling (with alphanumeric prefixes)
    pattern = '^(\D+)(\d+)'
    r = re.compile(pattern)
    matches = r.match(patent['number'])
    if matches:
        patent['number-type'] = matches.group(1)
        patent['number-real'] = matches.group(2)


def modify_invalid_patent_number(patent_number):

    # handle special cases (corrupted data?) like "WOWO 99/39395" or "USUS5650746A" (2008-01-23)
    patent_number = patent_number.replace('WOWO', 'WO')
    patent_number = patent_number.replace('USUS', 'US')
    patent_number = patent_number.replace('USDES', 'USD')

    # remove invalid characters
    #r_invalid = re.compile('[\W_]')
    r_invalid = re.compile('[\s_/-]')
    patent_number = r_invalid.sub('', patent_number)

    # make all characters uppercase
    patent_number = patent_number.upper()

    return patent_number

def encode_epodoc_number(document, options=None):
    options = options or {}
    thing = document.country + document.number
    if document.kind and not ('nokind' in options and options['nokind']):
        thing += '.' + document.kind
    return thing

