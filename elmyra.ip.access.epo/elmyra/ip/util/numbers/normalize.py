# -*- coding: utf-8 -*-
# (c) 2007-2011 ***REMOVED***
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from elmyra.ip.util.numbers.denormalize import denormalize_patent_wo
import re
import types
from elmyra.ip.util.numbers.helper import pad_left, trim_leading_zeros, fullyear_from_year
from elmyra.ip.util.numbers.common import split_patent_number, join_patent

"""
Normalize patent- and document-numbers.
"""


def patch_patent(patent):

    if patent:
        patched = patent.copy()

        # strip leading zeros of *publication* to 6 digits, if seqnumber is longer than 6 digits
        # examples: publication: AT401234; application: AT 967/1994 => AT96794
        if patched['country'] == 'AT':
            if len(patched['number']) > 6 and not '/' in patched['number']:
                patched['number'] = trim_leading_zeros(patched['number'])
                patched['number'] = pad_left(patched['number'], '0', 6)

        elif patched['country'] == 'AU':
            patched = normalize_patent_au(patched)

        # strip leading zeros with exception of kindcode == T1, then pad to 7 digits like EP
        # "Veröffentlichung der europäischen Patentanmeldung"
        elif patched['country'] == 'DE':
            patched['number'] = trim_leading_zeros(patched['number'])
            if patched.get('kind') == 'T1':
                patched['number'] = pad_left(patched['number'], '0', 7)

        # pad to 7 characters with leading zeros
        elif patched['country'] == 'EP':
            patched['number'] = trim_leading_zeros(patched['number'])
            patched['number'] = pad_left(patched['number'], '0', 7)

        # pad to 8 characters with leading zeros
        elif patched['country'] == 'IT':
            patched['number'] = trim_leading_zeros(patched['number'])
            patched['number'] = pad_left(patched['number'], '0', 8)

        # 2009-11-09: JP numbers
        elif patched['country'] == 'JP':
            patched = normalize_patent_jp(patched)

        # 2007-07-26: US applications are 4+7
        elif patched['country'] == 'US':
            patched = normalize_patent_us(patched)

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
            pass

        #print "patched (regular):", patent, patched
        return patched

    return patent


def normalize_patent(number, as_dict = False, as_string = False):

    # 1. handle patent dicts or convert (split) from string
    if type(number) == types.DictType:
        patent = number
    else:
        patent = split_patent_number(number)

    # 2. normalize patent dict
    patent_normalized = patch_patent(patent)

    # 3. result handling

    # 3.a) default mechanism: return what we've got
    if type(number) == types.DictType:
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
        patched = patent.copy()

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

    patched = patent.copy()

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

    patched = patent.copy()
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



def normalize_patent_us(patent):

    # USPTO number formats

    # PATFT - Issued Patents:
    # http://patft.uspto.gov/netahtml/PTO/srchnum.htm
    #
    #   Utility                           --  5,146,634 6923014 0000001
    #   Design                            -- 	D339,456 D321987 D000152
    #   Plant                             -- 	PP08,901 PP07514 PP00003
    #   Reissue                           -- 	RE35,312 RE12345 RE00007
    #   Defensive Publication             -- 	T109,201 T855019 T100001
    #   Statutory Invention Registration  -- 	H001,523 H001234 H000001
    #   Re-examination                    -- 	RX12
    #   Additional Improvement            -- 	AI00,002 AI000318 AI00007

    # AppFT - Patent Applications
    # http://appft.uspto.gov/netahtml/PTO/srchnum.html
    #
    #   Utility: 20010000044

    assert patent['country'] == 'US'

    patched = patent.copy()

    # filter: special document handling (with alphanumeric prefixes)
    # trim and pad sequential number with zeros to get total length of 7 characters for patent number
    pattern = '^(\D+)(\d+)'
    r = re.compile(pattern)
    matches = r.match(patched['number'])
    if matches:
        subtype = matches.group(1)
        seqnumber = matches.group(2)
        if subtype in ('D', 'PP', 'RD', 'RE', 'T', 'H', 'AI'):
            patched['number'] = subtype + pad_left(trim_leading_zeros(seqnumber), '0', 7 - len(subtype))
        return patched

    length = len(patched['number'])

    # US applications: convert from 4+5 or 4+6 to 4+7=11
    if length == 9 or length == 10:
        padding = '0' * (11 - length)
        patched['number'] = patched['number'][0:4] + padding + patched['number'][4:]

    # US patents: trim to seven digits
    else:
        patched['number'] = trim_leading_zeros(patched['number'])
        #patched['number'] = pad_left(patched['number'], '0', 7)

    return patched


def normalize_patent_jp(patent):
    """
    Normalizes to JP patent number format (FulltextPROO)
    http://www.cas.org/training/stneasytips/patentnumber2.html#anchor3
    """

    assert patent['country'] == 'JP'

    patched = patent.copy()

    r = re.compile('[\/|-]')
    parts = r.split(patched['number'])

    # handle special formatting like "JP8-179521"
    #sys.stderr.write(str(parts) + "\n")
    #sys.exit()
    if len(parts) == 2:
        patched['number'] = pad_left(parts[0], '0', 2) + pad_left(parts[1], '0', 6)

    # 2014-10-04: strip leading zeros (DEPATISnet yields numbers like JP002011251389A)
    else:
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

    patched = patent.copy()


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
        ]

    print "-" * 30
    print "original\tnormalized"
    print "-" * 30
    for number in numbers:
        if number.find('---') != -1:
            print number
            continue
        result = normalize_patent(number)
        #result = join_patent(patch_patent_old_archive(patent))
        print "%s\t%s" % (number, result)

if __name__ == "__main__":
    test_normalization()
