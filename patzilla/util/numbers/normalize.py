# -*- coding: utf-8 -*-
# (c) 2007-2018 Andreas Motl <andreas.motl@ip-tools.org>
import re
import types
import logging
from copy import copy
from patzilla.util.numbers.denormalize import denormalize_patent_wo
from patzilla.util.numbers.helper import pad_left, trim_leading_zeros, fullyear_from_year
from patzilla.util.numbers.common import decode_patent_number, split_patent_number, join_patent


logger = logging.getLogger(__name__)


"""
Normalize patent- and document-numbers.
"""

def patch_patent(patent, provider=None):

    if not patent:
        return

    number_length = len(patent['number'])

    patched = copy(patent)
    #print 'patched:', patched

    # strip leading zeros of *publication* to 6 digits, if seqnumber is longer than 6 digits
    # examples: publication: AT401234; application: AT 967/1994 => AT96794
    if patched['country'] == 'AT':
        """
        if len(patched['number']) > 6 and not '/' in patched['number']:
            patched['number'] = trim_leading_zeros(patched['number'])
            patched['number'] = pad_left(patched['number'], '0', 6)
        """
        patched['number'] = trim_leading_zeros(patched['number'])

    # pad to 6 characters with leading zeros
    elif patched['country'] == 'AR':
        patched['number'] = patched['number'].lstrip('0').rjust(6, '0')

    elif patched['country'] == 'AU':
        patched = normalize_patent_au(patched)

    elif patched['country'] == 'BR':
        patched['number'] = patched['number'].lstrip('0')

    # strip leading zeros with exception of kindcode == T1, then pad to 7 digits like EP
    # "Veröffentlichung der europäischen Patentanmeldung"
    elif patched['country'] == 'DE':
        patched['number'] = trim_leading_zeros(patched['number'])
        #if patched.get('kind') == 'T1':
        #    patched['number'] = pad_left(patched['number'], '0', 7)

    # The Eurasian Patent Organization (EAPO)
    # Pad to 6 characters with leading zeros
    elif patched['country'] == 'EA' and number_length < 9:
        patched['number'] = trim_leading_zeros(patched['number'])
        patched['number'] = pad_left(patched['number'], '0', 6)

    # pad to 7 characters with leading zeros
    elif patched['country'] == 'EP':
        patched['number'] = trim_leading_zeros(patched['number'])
        patched['number'] = pad_left(patched['number'], '0', 7)

    elif patched['country'] == 'GE':
        patched['number'] = patched['number'].lstrip('0')

        # e.g.
        # GE00U200501210Y = GEU20051210Y
        # GE00P200503700B = GEP20053700B
        #print '77777777777:', patched['number'][5]
        if patched['number'][5] == '0':
            patched['number'] = patched['number'][:5] + patched['number'][6:]


    elif patched['country'] == 'IT':
        patched['number'] = patched['number'].lstrip('0')
        patched = normalize_patent_it(patched)

    # 2017-09-06: KR numbers
    # e.g. KR1020150124192A => KR20150124192A
    elif patched['country'] == 'KR':
        patched['number'] = trim_leading_zeros(patched['number'])
        if len(patched['number']) > 11 and patched['number'][:2] == '10':
            patched['number'] = patched['number'][2:]

    # 2009-11-09: JP numbers
    elif patched['country'] == 'JP':
        patched = normalize_patent_jp(patched)

    # 2015-09-01: SE numbers
    elif patched['country'] == 'SE':
        patched = normalize_patent_se(patched)
        patched['number'] = trim_leading_zeros(patched['number'])

    # 2007-07-26: US applications are 4+7
    elif patched['country'] == 'US':
        patched = normalize_patent_us(patched, provider=provider)

    # normalize wo numbers to 4+6 format
    elif patched['country'] == 'WO':
        # WOPCT/US86/01765 or WOEP/2004/008531
        if patched['number'].startswith('PCT'):
            patched = normalize_patent_wo_pct(patched)
        else:
            patched = normalize_patent_wo(patched)
            #patched = denormalize_patent_wo(patched)

    # strip leading zeros
    else:
        patched['number'] = trim_leading_zeros(patched['number'])

    #print "patched (regular):", patent, patched
    return patched


def fix_patent_kindcode_ops(patent):
    """
    e.g. AT362828E should be returned as AT362828T for querying at OPS
    """

    if not patent:
        return

    if patent['country'] == 'AT' and patent['kind'] == 'E':
        patent['kind'] = 'T'

    elif patent['country'] == 'DE':
        if not patent['number'].isdigit(): return
        patent_number = int(patent['number'])

        # e.g. DE000000121107A, DE000000801283B
        if patent_number < 1000000:
            if patent['kind'] == 'A':
                patent['kind'] = 'C'
            elif patent['kind'] == 'B':
                patent['kind'] = 'C'

        # e.g. DE000001020931A
        elif 1000000 <= patent_number < 1400000:
            if patent['kind'] == 'A':
                patent['kind'] = 'B'

        # e.g. DE000002363448A
        elif 1400000 <= patent_number:
            if patent['kind'] == 'A':
                patent['kind'] = 'A1'

    elif patent['country'] == 'ES' and patent['kind'] == 'Y2':
        patent['kind'] = 'Y'

    elif patent['country'] == 'US' and patent['kind'] == 'E':
        if 'RE' not in patent['number']:
            patent['number'] = 'RE' + patent['number']


def depatisconnect_alternatives(number):
    """reverse "fix_patent" for DE documents"""

    # always add original number first
    numbers = [number]

    patent = split_patent_number(number)
    if patent['country'] == 'DE':
        if not patent['number'].isdigit():
            return [join_patent(patent)]

        patent_number = int(patent['number'])
        # e.g. DE000000121107A, DE000000801283B
        if patent_number < 1000000:
            if patent['kind'] == 'C':
                patent['kind'] = 'B'
                numbers.append(join_patent(patent))
                patent['kind'] = 'A'
                numbers.append(join_patent(patent))

        # e.g. DE000001020931A
        elif 1000000 <= patent_number < 1400000:
            #numbers.append(join_patent(patent))
            pass

        # e.g. DE000002363448A
        elif 1400000 <= patent_number:
            if patent['kind'] == 'A1':
                patent['kind'] = 'A'
                numbers.append(join_patent(patent))

    return numbers


def normalize_patent(number, as_dict=False, as_string=False, fix_kindcode=False, for_ops=True, provider=None):

    if provider is None and for_ops is True:
        provider = 'ops'

    # 1. handle patent dicts or convert (split) from string
    if isinstance(number, types.DictionaryType):
        patent = number
    else:
        patent = split_patent_number(number)

    # 2.a. normalize patent dict
    patent_normalized = patch_patent(patent, provider=provider)

    # 2.b. apply fixes
    if fix_kindcode:
        fix_patent_kindcode_ops(patent_normalized)

    # 3. result handling

    # 3.a) default mechanism: return what we've got
    if isinstance(number, types.DictionaryType):
        result = patent_normalized
    else:
        result = join_patent(patent_normalized)

    # 3.b) extended mechanism: return what we are requested for
    if as_dict:
        result = patent_normalized
    elif as_string:
        result = join_patent(patent_normalized)

    return result


def patch_patent_old_archive(patent):
    if patent:
        patched = copy(patent)

        if patched['country'] == 'WO':
            patched = denormalize_patent_wo(patched)

        # from patlib.inc.php (new 2005-03-18):
        # check for more files returned under certain circumstances
        # e.g. query for "US2005015034A1" returns "US_20050015034_A1.pdf"
        # Wenn die ersten vier Ziffern eine Jahreszahl sind, dann danach "0" einfügen
        elif patched['country'] == 'US':
            """
            if int(patched['number'][0:4]) >= 1900 and len(patched['number'][4:]) < 7:
              patched['number'] = patched['number'][0:4] + '0' + patched['number'][4:]
            """
            # 2007-07-26: US applications are 4+7
            patched = normalize_patent_us(patched)


        # pad to 8 characters with leading zeros; this is the worst thing ever
        patched['number'] = pad_left(patched['number'], '0', 8)

        #print "patched (old):", patent, patched
        return patched


def normalize_patent_wo(patent):
    """
    Normalizes to "WIPO Publication Number" format, e.g. WO2005092324

    see "Pub. No.":
    http://www.wipo.int/pctdb/en/wo.jsp?IA=WO/2005/092324
    http://www.wipo.int/pctdb/en/wo.jsp?IA=WO0067640
    """

    assert patent['country'] == 'WO'

    patched = copy(patent)

    # filter: leave special documents untouched (with alphanumeric prefix)
    pattern = '^\D+'
    r = re.compile(pattern)
    if r.match(patched['number']):
        return patched

    length = len(patent['number'])

    # convert from 2+5 or 2+6 to 4+6
    if length == 7 or length == 8:

        year = patched['number'][0:2]
        seqnumber = patched['number'][2:]

        # assume for century: 78-99 => 19, otherwise => 20
        # build fullyear from (2-digit) year
        fullyear = fullyear_from_year(year)

        """
        # try different decoding: 1 zero + 2 year + 5 seqnumber
        # (wrong format due to "pad everything to 8 characters" logic of Bestellsystem)
        # so strip off first leading zero before decoding again
        # TODO: what about WO09802618A2, WO00202618A2, WO00402618A2, WO09201000A1, WO09901000A3, WO00101000A1?
        if length == 8:

          # 1. numbers like WO00101000A1 are ambiguous, could be WO2000101000A1 or WO2001001000A1
          ambiguous_2000_2003 = ( 2000 <= int(fullyear) and int(fullyear) <= 2003 and patched['number'].startswith('00') )

          # 2. same with 8 digit numbers >= 2004, starting with "WO004..."
          #    hint: WO00402618A2 can not be WO2000402618A2 (due to format 2+6 and release date), so must be WO2004002618A2
          ambiguous_2004_bis  = ( int(fullyear) >= 2004 )

          if ambiguous_2000_2003:  # or ambiguous_2004_bis:
            patched['number'] = patched['number'][1:]
            year = patched['number'][0:2]
            seqnumber = patched['number'][2:]
            fullyear = fullyear_from_year(year)
        """

        #if length == 8 and patched['number'].startswith('0') and int(fullyear) < 2003:
        #    return


        # pad sequential number to 6 characters
        patched['number'] = fullyear + pad_left(seqnumber, '0', 6)


    # convert from 4+5 to 4+6 (wrong format)
    elif length == 9:
        fullyear = patched['number'][0:4]
        seqnumber = patched['number'][4:]

        # pad sequential number to 6 characters
        patched['number'] = fullyear + pad_left(seqnumber, '0', 6)


    patched['number'] = trim_leading_zeros(patched['number'])
    return patched


def normalize_patent_wo_pct(patent):
    """
    Normalizes to "WIPO Application Number" format, e.g. PCT/US2005/009417
    Takes inputs like WOPCT/US02/03226, PCT/US1999/9417 or WOEP/2004/008531

    see "International Application No.":
    http://www.wipo.int/pctdb/en/wo.jsp?IA=PCT/US2005/009417
    http://www.wipo.int/pctdb/en/wo.jsp?IA=US2005009417

    see also:
    http://www.wipo.int/edocs/pctdocs/en/2005/pct_2005_42-section3.pdf
    """

    assert patent['country'] == 'WO'

    patched = copy(patent)
    #print patched

    r = re.compile('[\/|-]')
    parts = r.split(patched['number'])

    # handle special formatting like "WOPCT/WO9831467": convert to WO publication number
    if len(parts) == 2:
        pct = parts[0]
        patent_number = parts[1]
        if patent_number.startswith('WO'):
            wo_patent = split_patent_number(patent_number)
            return normalize_patent_wo(wo_patent)

    # only allow numbers containing three segments
    if not len(parts) == 3:
        return


    # assign segment names
    pct = parts[0]
    country_year = parts[1]
    seqnumber = parts[2]

    # handle special formatting like "WOPCT-WO97/29690": convert to WO publication number
    if country_year.startswith('WO'):
        wo_patent = split_patent_number(country_year + seqnumber)
        return normalize_patent_wo(wo_patent)

    # handle special formatting like "WOEP/2004/008531"
    if pct.startswith('WO') and len(pct) == 4:
        country_year = pct[2:4] + country_year

    # assume s.th. like "EP02": expand year to full year
    if len(country_year) == 4:
        # assume for century: 78-99 => 19, otherwise => 20
        # build fullyear from (2-digit) year
        fullyear = fullyear_from_year(country_year[2:])
        country_year = country_year[0:2] + fullyear

    # pad sequential number to six digits with leading zeros
    seqnumber = pad_left(seqnumber, '0', 6)

    # delete country,
    patched['country'] = ''
    patched['number'] = ('%s/%s/%s' % (pct, country_year, seqnumber))

    return patched



def normalize_patent_us(patent, provider=None):
    """
    # TODO:
    # >>> DocumentIdentifier('US2548918').normalize(provider=DocumentProvider.USPTO).serialize()
    >>> normalize_patent_us(decode_patent_number('US2548918'), provider='uspto').serialize()
    'US02548918'
    """

    # USPTO number formats

    # PATFT - Issued Patents:
    # http://patft.uspto.gov/netahtml/PTO/srchnum.htm
    #
    #   Utility                           --   5,146,634 6923014 0000001
    #   Design                            --    D339,456 D321987 D000152
    #   Plant                             --    PP08,901 PP07514 PP00003
    #   Reissue                           --    RE35,312 RE12345 RE00007
    #   Defensive Publication             --    T109,201 T855019 T100001
    #   Statutory Invention Registration  --    H001,523 H001234 H000001
    #   Re-examination                    --    RX12
    #   Additional Improvement            --    AI00,002 AI000318 AI00007
    subtype_prefixes = ['D', 'PP', 'RD', 'RE', 'T', 'H', 'AI']

    # AppFT - Patent Applications
    # http://appft.uspto.gov/netahtml/PTO/srchnum.html
    #
    #   Utility: 20010000044

    assert patent['country'] == 'US'

    patched = copy(patent)

    length = len(patched['number'])

    if provider == 'ops' or provider == 'espacenet':

        # OPS accepts US patent application publication numbers in 4+6=10 format
        # Examples: US2015322651A1, US2017250417A1, US2017285092A1

        # 2017-10-25
        # DEPATISnet started delivering application publication numbers in 5+7 format
        # with a leading zero after the country, e.g. US000006166174A, US020170285092A1
        # around October 2017. Account for that.
        if length == 12:
            patched['number'] = patched['number'].lstrip('0')
            length = len(patched['number'])

        # US application publication numbers: Convert from 4+5=9 to 4+6=10
        if length == 9:
            padding = '0' * (10 - length)
            patched['number'] = patched['number'][0:4] + padding + patched['number'][4:]

        # US application publication numbers: Convert from 4+7=11 to 4+6=10
        # 2015-12-20: Normalize responses from SIP like "US20150322651A1" to "US2015322651A1"
        elif length == 11:
            if patched['number'][4] == '0':
                patched['number'] = patched['number'][0:4] + patched['number'][5:]

        # US patents: Handle document numbers with character prefixes
        # Trim leading zeros for OPS
        elif 'number-type' in patched and 'number-real' in patched:
            subtype = patched['number-type']
            seqnumber = patched['number-real']
            if subtype in subtype_prefixes:
                patched['number'] = subtype + trim_leading_zeros(seqnumber)

        # US patents: Strip leading zeros
        else:
            patched['number'] = patched['number'].lstrip('0')

    else:

        # US patents: Handle document numbers with character prefixes
        # Pad patent number with zeros to get total length of 7 characters
        if 'number-type' in patched and 'number-real' in patched:
            subtype = patched['number-type']
            seqnumber = patched['number-real']
            if subtype in subtype_prefixes:
                patched['number'] = subtype + seqnumber.zfill(7)

        # Convert from 4+5=9 or 4+6=10 to 4+7=11
        # US20170000054A1
        elif length == 9 or length == 10:
            padding = '0' * (11 - length)
            patched['number'] = patched['number'][0:4] + padding + patched['number'][4:]

    # 2018-04-23: Espacenet changed behavior, handle edge case for
    # USD813591S to yield https://worldwide.espacenet.com/publicationDetails/claims?CC=US&NR=D813591S&KC=S
    if provider == 'espacenet':
        if 'number-type' in patched:
            if patched['number-type'] == 'D' and patched['kind'] == 'S':
                patched['number'] += patched['kind']

    # 2019-03-05: When going to the USPTO itself, pad sequential number to 8 digits.
    if provider == 'uspto':
        patched['number'] = patched['number'].zfill(8)

    return patched


def normalize_patent_jp(patent):
    """
    Normalizes to JP patent number format (JPO)
    - http://www.epo.org/searching/asian/japan/numbering.html
    - http://www.cas.org/training/stneasytips/patentnumber2.html#anchor3 "Japanese emperor year numbering restart format"

    SHOWA (SHO, S) - reign of Emperor Hirohito
    1926 to 1989
    Japanese emperor year: 01-64
    conversion: Western Year - 25

    HEISEI (HEI, H) - reign of Emperor Akihito
    1989 to 2000
    Japanese emperor year: 01-12
    conversion: Western Year - 88

    Decision: In ambiguity case, let's favor H over S, so very old Japanese documents (1926-1938) get suppressed.

    Examples:
    - Something yields JP8-179521, which OPS will only accept as JPH08179521
    - "SIP" yields JP58002167U, which OPS will only accept as JPS582167U
    - JP3657641B2 should stay the same
    - JP08007001AA should become JP08007001A

    The JPO no longer uses the era name for the publication numbers after 2000 (Heisei-12),
    and therefore, we will not see the new era name “Reiwa” on publication numbers.
    -- https://allegropat.com/new-era-reiwa-starts-in-japan-from-may-1-2019/
    """

    assert patent['country'] == 'JP'

    patched = copy(patent)

    #print patched['number']

    # new format, don't touch; e.g. JP2011251389A
    if len(patched['number']) == 10:
        return patched

    # 2014-11-12: handle numbers without emperor year symbols
    if patched['number'][0] not in ['S', 'H']:

        # handle special formatting like "JP8-179521"
        if '-' in patched['number'] or '/' in patched['number']:
            parts = re.split('[\/|-]', patched['number'])
            if len(parts) == 2:
                patched['number'] = parts[0].rjust(2, '0') + parts[1].rjust(6, '0')

        if len(patched['number']) == 8 and not patched['kind'].startswith('B'):
            emperor_year = patched['number'][:2]
            real_number = patched['number'][2:]
            if int(emperor_year) <= 12:
                emperor_symbol = 'H'
            else:
                emperor_symbol = 'S'

            patched['number'] = emperor_symbol + emperor_year.rjust(2, '0') + real_number.lstrip('0')

            # 2015-09-01: mogrify kindcodes for edge cases, here: JP08007001AA => JPH087001A
            if patched['kind'] == 'AA':
                patched['kind'] = 'A'

    # 2014-10-04: strip leading zeros (DEPATISnet yields numbers like JP002011251389A or JP00000S602468B2)
    patched['number'] = patched['number'].lstrip('0')

    return patched


def normalize_patent_au(patent):
    """
    Normalizes "Australian" format, e.g. AU2003212220A1, AU200042655B2, AU00784257B2

    Patent Application Number:
      old: 4+5 digits  (Patadmin, before 5 July 2002)
      new: 4+6 digits  (PAMS, after 5 July 2002)
      http://apa.hpa.com.au:8080/ipapa/intro
      http://pericles.ipaustralia.gov.au/aub/aub_pages_1.intro
    Patent Number:
      6 digits
      http://pericles.ipaustralia.gov.au/aub/aub_pages_1.intro
    """

    assert patent['country'] == 'AU'

    patched = copy(patent)


    length = len(patent['number'])

    # convert from 4+5 to 4+6 (old to new format)
    if length == 9:
        fullyear = patched['number'][0:4]
        seqnumber = patched['number'][4:]

        # pad sequential number to 6 characters
        patched['number'] = fullyear + pad_left(seqnumber, '0', 6)

    else:
        patched['number'] = trim_leading_zeros(patched['number'])

    if len(patched['number']) < 6:
        patched['number'] = pad_left(patched['number'], '0', 6)

    return patched


def normalize_patent_it(patent):

    #
    # Italian number formats
    #
    # IT000009015161U => IT9015161U
    # IT000001259603B => IT1259603B
    # ITVR0020130124A => ITVR20130124A
    # ITVE0020080094A => ITVE20080094A
    #

    assert patent['country'] == 'IT'

    patched = copy(patent)

    # filter: special document handling (with alphanumeric prefixes)
    # trim and pad sequential number with zeros to get total length of 7 characters for patent number
    if patched.has_key('number-type') and patched.has_key('number-real'):
        subtype = patched['number-type']
        seqnumber = patched['number-real']
        patched['number'] = subtype + seqnumber.lstrip('0')
        return patched

    return patched


def normalize_patent_se(patent):
    """
    Normalize SE patent number format
    """

    assert patent['country'] == 'SE'

    patched = copy(patent)

    #print patched['number']

    # 2015-09-01: mogrify kindcodes for patents from sweden, here: SE9503964A => SE9503964L
    # TODO: don't modify, add it to a variants list, as soon as we have a similar subsystem to "EP Archive Service" here
    if patched['kind'] == 'A':
        patched['kind'] = 'L'

    return patched


def test_normalization():
    numbers = [

        '--- from production',
        #'USD0558961',
        #'WODM 055039',
        #'DEM 89 08 812',
        #'USRE039998E1',
        # ...
        # ...
        'AT 967/1994',
        'AT 401 234 B',
        'AT 001 234 B',
        'DE000019630877C2',
        'JP002011251389A',
        'JP00000S602468B2',
        'JP8-179521',
        'JP58002167U',
        'JP3657641B2',
    ]

    print "-" * 30
    print '{0}{1}'.format("original".ljust(20), "normalized")
    print "-" * 30
    for number in numbers:
        if number.find('---') != -1:
            print number
            continue
        result = normalize_patent(number)
        #result = join_patent(patch_patent_old_archive(patent))
        print "{0}{1}".format(number.ljust(20), result)

if __name__ == "__main__":
    test_normalization()
