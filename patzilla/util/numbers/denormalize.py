# -*- coding: utf-8 -*-
# (c) 2007,2014 Andreas Motl <andreas.motl@elmyra.de>
from patzilla.util.numbers.helper import pad_left, fullyear_from_year
from patzilla.util.numbers.common import join_patent, split_patent_number

"""
Denormalize patent- and document-numbers.
"""

def denormalize_patent(patent):
    if patent:
        patched = patent.copy()

        # denormalize wo numbers to according format (2+5, 2+6 or 4+6)
        if patched['country'] == 'WO':
            patched = denormalize_patent_wo(patched)

        return patched


def denormalize_patent_wo(patent):
    assert patent['country'] == 'WO'

    patched = patent.copy()

    length = len(patent['number'])

    # convert from 4+6 to 2+5 ...
    if length == 10:

        fullyear = patched['number'][0:4]
        century = fullyear[0:2]
        seqnumber = patched['number'][4:]

        # ... for fullyear == 19*: convert to 2+5
        if century == '19':
            seqnumber = str(int(seqnumber))
            patched['number'] = fullyear[2:4] + pad_left(seqnumber, '0', 5)

        # ... for fullyear == 20*
        if century == '20':
            patched['number'] = denormalize_patent_wo_algo(int(fullyear), int(seqnumber))


    # convert from 2+6 to 2+5 ...
    elif length == 8:

        year = patched['number'][0:2]
        seqnumber = patched['number'][2:]

        fullyear = fullyear_from_year(year)
        #print fullyear
        #print patched['number']
        patched['number'] = denormalize_patent_wo_algo(int(fullyear), int(seqnumber))
        #print patched['number']


    # wrong format: assume 4+5, convert to 2+5 ...
    elif length == 9:
        fullyear = patched['number'][0:4]
        seqnumber = patched['number'][4:]
        patched['number'] = denormalize_patent_wo_algo(int(fullyear), int(seqnumber))


    return patched

def denormalize_patent_wo_algo(fullyear, seqnumber):

    """
    Nummernanalyse WO:

      Übergang von 2+5 zu 2+6:
      WO=02/51230
      WO=02/051231

      Übergang von 2+6 zu 4+6:
      WO03107732   (24.12.2003)
      WO2004000001 (31.12.2003)
    """

    # 2+5
    if fullyear <= 2001 or (fullyear == 2002 and seqnumber <= 51230):
        number = str(fullyear)[2:4] + pad_left(seqnumber, '0', 5)

    # 2+6
    elif (fullyear == 2002 and seqnumber >= 51231) or (fullyear == 2003):
        number = str(fullyear)[2:4] + pad_left(seqnumber, '0', 6)

    # 4+6
    else:
        number = str(fullyear) + pad_left(seqnumber, '0', 6)

    return number


def test_denormalization():

    payload = """
WO2002051230
WO2002051231
WO2006113621A3
WO1998016331A3
WO2000001014A1
WO2001002000A3
WO1999012345
WO1999123456
WO2001012345
WO2001098623A1
WO2001098623A1
WO2001098623A1
WO2001098623A1
WO2003107732
WO2003107732
WO2004000001
WO1999013800
WO1999023997
WO1990004917
WO2000027301
WO2000000748
WO2003043359
WO2003107520
WO2007054055
---
WO1990004917
"""

    print "-" * 30
    print "original\tdenormalized"
    print "-" * 30
    for number in payload.split("\n"):
        if not number or number == "\n": continue
        if number.startswith('---'):
            print number
            continue
        number_denormalized = join_patent(denormalize_patent(split_patent_number(number)))
        print "%s\t%s" % (number, number_denormalized)


if __name__ == "__main__":
    test_denormalization()
