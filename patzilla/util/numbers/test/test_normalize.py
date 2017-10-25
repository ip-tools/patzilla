# -*- coding: utf-8 -*-
# (c) 2009,2015-2017 Andreas Motl <andreas.motl@elmyra.de>
from collections import OrderedDict
from patzilla.util.numbers.normalize import normalize_patent


t = OrderedDict()

# amo
t['EP666666B1']     = 'EP0666666B1'
t['EP1000000']      = 'EP1000000'

t['EP7054A1']       = 'EP0007054A1'
t['EP0007054A1']    = 'EP0007054A1'
t['EP00007054A1']   = 'EP0007054A1'

t['DE10142737B4 ']  = 'DE10142737B4'
t['WO2006113621A3'] = 'WO2006113621A3'
t[' WO199816331A3'] = 'WO1998016331A3'
t['WO00001014A1']   = 'WO2000001014A1'
t['WO01002000A3']   = 'WO2001002000A3'
t['WO9912345']      = 'WO1999012345'
t['WO99123456']     = 'WO1999123456'
t['WO0112345']      = 'WO2001012345'
t['US07318131B2']   = 'US7318131B2'

# examples from günther
t['WO0198623A1']    = 'WO2001098623A1'      # original (from publication date and inside pdf): 2+5
t['WO01098623A1']   = 'WO2001098623A1'      # wrong as of publication date: 2+6
t['WO2001098623A1'] = 'WO2001098623A1'      # normalized: 4+6
t['WO200198623A1']  = 'WO2001098623A1'      # definitively wrong: 4+5
t['WO2001098623A1'] = 'WO2001098623A1'      # wrong: 4+6, but wrong publication date; should be 2+5
t['WO200946303']    = 'WO2009046303'        # 4+5
t['WO03107732']     = 'WO2003107732'
t['WO2003107732']   = 'WO2003107732'
t['WO2004000001']   = 'WO2004000001'
t['WO99/13800']     = 'WO1999013800'

# examples from nora (also aus jeder periode mit und ohne 0 auffüllung eine)
t['WO 9923997']     = 'WO1999023997'
t['WO 9004917']     = 'WO1990004917'
t['WO 0027301']     = 'WO2000027301'
t['WO 0000748']     = 'WO2000000748'
t['WO 03043359']    = 'WO2003043359'
t['WO 03107520']    = 'WO2003107520'
t['WO 2007054055']  = 'WO2007054055'
t['US20010003540']  = 'US2001003540'
t['US2001003540']   = 'US2001003540'
t['US200103540']    = 'US2001003540'

# EPD
t['US07317210B2']    = 'US7317210B2'
t['AT409 902B']      = 'AT409902B'
t['DE31 00 442C1']   = 'DE3100442C1'
t['EP1083612']       = 'EP1083612'
t['EP083612']        = 'EP0083612'
t['EP0 240 590B1']   = 'EP0240590B1'
t['GB2 000 685A']    = 'GB2000685A'
t['JP2000182770A']   = 'JP2000182770A'
t['JP8-179521']      = 'JPH08179521'        # bei günther nachfragen
t['JP05-142789']     = 'JPH05142789'        # bei günther nachfragen
t['JP2000-347427']   = 'JP2000347427'       # bei günther nachfragen
t['KR2001-0024348']  = 'KR20010024348'
t['WOWO 99/39395']   = 'WO1999039395'
t['WOWO00/05701']    = 'WO2000005701'
t['US147451A']       = 'US147451A'
t['US0147451A']      = 'US147451A'
#t['US100147451A']    = 'US100147451A'          # PRÜFEN!

t['US2002/0066904A1']= 'US2002066904A1'
t['US6147451A']      = 'US6147451A'
t['US147451A']       = 'US147451A'
t['USD281167S']      = 'USD281167S'
t['USUS5650746A']    = 'US5650746A'
t['USDES374176S']    = 'USD374176S'
t['US60/609868A']    = 'US60609868A'
t['US09/930611A']    = 'US9930611A'

# fantasy
t['USD123456789']    = 'USD123456789'
t['USRE123456789']   = 'USRE123456789'
t['USRE1234E1']      = 'USRE1234E1'
t['US6147451A']      = 'US6147451A'

# from production
t['USD0558961']          = 'USD558961'
t['WODM 055039']         = 'WODM055039'         # see http://www.freepatentsonline.com/D558991.html
t['DEM 89 08 812']       = 'DEM8908812'

t['USRE039998E1']        = 'USRE39998E1'
t['USD000123456']        = 'USD123456'
t['USD1234']             = 'USD1234'
t['USRX12']              = 'USRX12'

t['WOPCT/WO9831467']     = 'WO1998031467'
t['WOPCT/US1999/02091']  = 'PCT/US1999/002091'
t['WOPCT/GB1999/01042']  = 'PCT/GB1999/001042'
t['WOPCT/EP02/07746']    = 'PCT/EP2002/007746'

t['WOPCT/US1999/02091']  = 'PCT/US1999/002091'
t['WOPCT/GB1999/01042']  = 'PCT/GB1999/001042'
t['WOPCT/EP02/07746']    = 'PCT/EP2002/007746'
t['WOPCT/EP02/07746']    = 'PCT/EP2002/007746'
t['WOPCT/US98/09178']    = 'PCT/US1998/009178'
t['WOPCT/AU95/00354']    = 'PCT/AU1995/000354'
t['WOPCT-WO97/29690']    = 'WO1997029690'
t['WOPCT-WO00/67640']    = 'WO2000067640'
t['WOPCT/FR98/02552']    = 'PCT/FR1998/002552'
t['WOWO2003-EP8824']     = None
t['IT19732A/88']         = None
t['WOPCT/CA98/00092']    = 'PCT/CA1998/000092'
t['WOPCT/CA98/00092']    = 'PCT/CA1998/000092'
t['JPHEI 3-53606']       = None
t['WOPCT/US02/03226']    = 'PCT/US2002/003226'
t['WOPCT/US2004/011130'] = 'PCT/US2004/011130'
t['WOPCT/US86/01765']    = 'PCT/US1986/001765'
t['WOPCT/US2004/003151'] = 'PCT/US2004/003151'

t['PCT/US99/009417']     = 'PCT/US1999/009417'
t['PCT/US1999/9417']     = 'PCT/US1999/009417'

# via: http://books.google.de/books?id=waOrACYzONMC&pg=PA91&lpg=PA91&dq=uspto+patent+number+format&source=bl&ots=tjJ3TgD9HH&sig=WUnhlkYPBaCYFJpgJNyptyEoMdE&hl=de&ei=WjD3SoTPCJzymwOEw4W0Aw&sa=X&oi=book_result&ct=result&resnum=3&ved=0CBEQ6AEwAg
t['US845948']            = 'US845948'           # appnum
t['US6990683']           = 'US6990683'          # pubnum
#t['WOEP/2004/008531']    = 'PCT/EP2004/008531'  # appnum
t['WO2005/098230']       = 'WO2005098230'       # pubnum
t['EP20020762866']       = 'EP20020762866'      # appnum
t['EP1333613']           = 'EP1333613'          # pubnum
# IPOS: appnum: 200507268-1, pubnum: 117045
t['JP100762']            = 'JP100762'           # appnum
t['JP1309841']           = 'JP1309841'          # pubnum
t['CN2172863']           = 'CN2172863'          # appnum
t['CN566528']            = 'CN566528'           # pubnum
# TIPO: appnum: 90121515, pubnum: 595092
t['GB20040008721']       = 'GB20040008721'      # appnum
t['GB2413271A']          = 'GB2413271A'         # pubnum
# KIPO: appnum: 1019980006278, pubnum: 100280219
# TIPIC: appnum: 13884, pubnum: 10674

# patlib.inc.php: get_patent_patched
t['US2005015034A1']      = 'US2005015034A1'

# from utils.py
t['WO00202618A2']        = 'WO2000202618A2'
t['WO00402618A2']        = 'WO2000402618A2'
t['WO0402618A2']         = 'WO2004002618A2'
t['WO09802618A2']        = 'WO2009802618A2'

# from archive
t['AT00256702B']         = 'AT256702B'
t['AT00009794U1']        = 'AT9794U1'
t['AT00008739U1']        = 'AT8739U1'

t['AU2003212220A1']      = 'AU2003212220A1'     # application
t['AU200042655B2']       = 'AU2000042655B2'     # application
t['AU200012345B2']       = 'AU2000012345B2'     # application, fantasy
t['AU20001234B2']        = 'AU20001234B2'       # application, fantasy
t['AU00784257B2']        = 'AU784257B2'         # patent
t['AU12345B2']           = 'AU012345B2'         # patent, fantasy
t['BE00571395A']         = 'BE571395A'
t['BE01010558A']         = 'BE1010558A'
t['CA02467000A1']        = 'CA2467000A1'
t['CA00946070A']         = 'CA946070A'
t['CH00671003A']         = 'CH671003A'
t['CH00014176A']         = 'CH14176A'
t['CN100494015C']        = 'CN100494015C'
t['CN01847039A']         = 'CN1847039A'
t['CS00277231B6']        = 'CS277231B6'
t['CZ00284347B6']        = 'CZ284347B6'
t['DD00283008B5']        = 'DD283008B5'
t['DD00070548A']         = 'DD70548A'
t['DD00009478A']         = 'DD9478A'

t['DE01071000B']         = 'DE1071000B'
t['DE10002000A1']        = 'DE10002000A1'
t['DE10002000A1']        = 'DE10002000A1'
t['DE102004002000A1']    = 'DE102004002000A1'
t['DE00700001A']         = 'DE700001C'          # 2015-01-13: behavior changed, now favoring OPS => kindcode A translates to C
t['DE000060018002T2']    = 'DE60018002T2'
t['DE00694003T1']        = 'DE694003T1'
t['DE00935004T1']        = 'DE935004T1'
t['DE00650009A']         = 'DE650009C'          # 2015-01-13: behavior changed, now favoring OPS => kindcode A translates to C
t['DE000019958011A1']    = 'DE19958011A1'
t['DE09422010U1']        = 'DE9422010U1'
t['DE000060126015T2']    = 'DE60126015T2'
t['DE00087015A']         = 'DE87015C'           # 2015-01-13: behavior changed, now favoring OPS => kindcode A translates to C
t['DE000004240017A1']    = 'DE4240017A1'
t['DE000004431018A1']    = 'DE4431018A1'
t['DE02309038A']         = 'DE2309038A1'        # 2015-01-13: behavior changed, now favoring OPS => kindcode A translates to A1

t['EP00169000A2']        = 'EP0169000A2'
t['EP01296000A3']        = 'EP1296000A3'

t['ES02292305A1']        = 'ES2292305A1'
t['FI00892230A']         = 'FI892230A'
t['FR02862000B1']        = 'FR2862000B1'
t['FR000002853021A1']    = 'FR2853021A1'
t['FR00809024A']         = 'FR809024A'
t['FR000002876313A1']    = 'FR2876313A1'

t['GB01464631A']         = 'GB1464631A'
t['GB02372000A']         = 'GB2372000A'
t['GB00898009A']         = 'GB898009A'
t['GB00440724A']         = 'GB440724A'

t['HU00224856B1']        = 'HU224856B1'
t['IT01247849B']         = 'IT1247849B'
t['JP04219000B2']        = 'JP4219000B2'
t['NL01015058C']         = 'NL1015058C'
t['PL00193102B1']        = 'PL193102B1'
t['RO00121297B1']        = 'RO121297B1'
t['RO00073665A1']        = 'RO73665A1'

t['RU02353337C2']        = 'RU2353337C2'
t['SE00523007C2']        = 'SE523007C2'
t['SU00205011A1']        = 'SU205011A1'

t['US01202000A1']        = 'US1202000A1'
t['US0340000A1']         = 'US340000A1'
t['US03548000A1']        = 'US3548000A1'
t['US0D337000S1']        = 'USD337000S1'
t['US0PP12001P2']        = 'USPP12001P2'
t['US0 340002A1']        = 'US340002A1'
t['US00000002B1']        = 'US2B1'
t['US00000002S1']        = 'US2S1'
t['US0RD15002E1']        = 'USRD15002E1'
t['US0RE15003E1']        = 'USRE15003E1'
t['US00404004S']         = 'US404004S'
t['US0PP12009P2']        = 'USPP12009P2'
t['USD459002S']          = 'USD459002S'

t['WO0001000A1']         = 'WO2000001000A1'
t['WO00001000A1']        = 'WO2000001000A1'
t['WO0010000A1']         = 'WO2000010000A1'
t['WO00010000A1']        = 'WO2000010000A1'
t['WO0101000A1']         = 'WO2001001000A1'
t['WO00101000A1']        = 'WO2000101000A1'
t['WO01002000A3']        = 'WO2001002000A3'
t['WO09201000A1']        = 'WO2009201000A1'
t['WO09901000A3']        = 'WO2009901000A3'
t['WO00000001A2']        = 'WO2000000001A2'
t['WO0000001A2']         = 'WO2000000001A2'
t['WO002006095001A1']    = 'WO2006095001A1'
t['WO03065003A2']        = 'WO2003065003A2'
t['WO002004096013A2']    = 'WO2004096013A2'
t['WO002000066014A1']    = 'WO2000066014A1'


# via espacenet:
t['AT 967/1994']         = 'AT967/1994'         # maybe 'AT96794'
t['AT 401 234 B']        = 'AT401234B'
t['AT 001 234 B']        = 'AT1234B'            # fantasy
t['AT0001 234 B']        = 'AT1234B'            # fantasy

# more
t['WO1A2']               = 'WO1A2'              # fantasy
t['US1A']                = 'US1A'               # fantasy
t['US000001A']           = 'US1A'               # fantasy
t['DE3A']                = 'DE3C'               # fantasy   # 2015-01-13: behavior changed, now favoring OPS => kindcode A translates to C
t['DE00000003A']         = 'DE3C'               # fantasy   # 2015-01-13: behavior changed, now favoring OPS => kindcode A translates to C
t['AT_00213320_B']       = 'AT213320B'
t['WO_09104034_A3']      = 'WO2009104034A3'
t['WO09104034A3']        = 'WO2009104034A3'
t['WO_9959827_A1']       = 'WO1999059827A1'
t['WO_9901000_A3']       = 'WO1999001000A3'
t['WO_09001000_A3']      = 'WO2009001000A3'
t['WO00009000A3']        = 'WO2000009000A3'
t['DE19964591']          = 'DE19964591'

t['WO002001002000A3']    = 'WO2001002000A3'
t['WO9222000A3']         = 'WO1992022000A3'
t['WO09222000A3']        = 'WO2009222000A3'

t['DE10001499.2']        = 'DE10001499.2'


# Elmyra

# via "B25B27/? and B62D65/?" (pages 13 and 16): BR000PI0507004A, BR000PI0502229A
t['BR000PI0507004A']     = 'BRPI0507004A'
t['BR000PI0502229A']     = 'BRPI0502229A'
t['MX00PA05006297A']     = 'MXPA05006297A'

# via "B25B27/? and B62D65/?": AT362828E
t['AT000362828E']        = 'AT362828T'

t['IT000009015161U']        = 'IT9015161U'
t['IT000001259603B']        = 'IT1259603B'
t['ITVR0020130124A']        = 'ITVR20130124A'
t['ITVE0020080094A']        = 'ITVE20080094A'

t['WO9619897A1']            = 'WO1996019897A1'
t['WO0069127A1']            = 'WO2000069127A1'
t['WO03063424A2']           = 'WO2003063424A2'

t['AR000000071041A1']       = 'AR071041A1'
t['AR000000060116A1']       = 'AR060116A1'
t['AR000000004605A1']       = 'AR004605A1'

t['GE00U200501210Y']        = 'GEU20051210Y'
t['GE00P200503700B']        = 'GEP20053700B'

german_kindcode_fixes = """

# Fazit:
# Bei U (Gebrauchsmustern) ist alles gut.

# DE+Nummer<1000000
# A: IPS: Hier muss eine Umsetzung A->C rein
# B: IPS: Hier muss eine Umsetzung B->C rein

# DE+Nummer>1000000 und <1400000
# A: IPS: Hier muss eine Umsetzung A->B rein
# B: OK

# DE+Nummer <1400000
# A: A->A1
# B: OK
# IPS: Funktioniert automatisch

# Details zum Test:
# DE Check alte DE Publikationen
# kommen beim EPO unter KindCode C

# 1900: (Nur A gefunden)
DE000000121107A = DE121107C
DE000000112245A= DE112245C

# 1920 (Nur A gefunden)
DE000000330860A=DE330860C

# 1930 (Nur A gefunden)
DE466541A=DE466541C

# 1940: (Nur A gefunden)
DE000000647068A=DE647068C

# IPS: Hier muss eine Umsetzung A->C rein


# 1946-1949 keine DE Schutzrechte beim DPMA


# 1950:
# (Kindcodes U, A, B)

DE000001617764U =DE1617764U
# IPS funktioniert

DE000000801283B = DE801283C
# IPS: Hier muss eine Umsetzung B->C rein

DE000000761063A = DE761063C
# IPS: Hier muss eine Umsetzung A->C rein


DE000P0001770BAZ = None
DE000Q0000001MAZ = None
DE000P0018311DAZ = None
# Hier kann ich nichts passendes bei Espacenet finden


# 1955
# (Kindcodes U, A, B)

DE000001710055U = DE1710055U
# IPS funktioniert

DE000000870319B = DE870319C
DE000000918770B = DE918770C
# IPS: Hier muss eine Umsetzung B->C rein

DE000000753891A = DE753891C
# IPS: Hier muss eine Umsetzung A->C rein


# 1956:
# (Kindcodes U, A, B)

# Exoten:
DE000SC010639MAZ = None
DE000SC010234MAZ = None
# Hier kann ich nichts passendes bei Espacenet finden

DE000001736208U = DE1736208U
# IPS funktioniert

DE000000956397B = DE956397C
DE000000949370B = DE949370C
# IPS: Hier muss eine Umsetzung B->C rein

DE000000750093A = DE750093C
# IPS: Hier muss eine Umsetzung A->C rein


# -----
# 1957:
DE000001020931B=DE1020931B
# IPS funktioniert

DE000001020931A=DE1020931B
DE000000752628A=DE752628C
DE000001017472A=DE1017472B
DE000001000991A=DE1000991B
DE000001001855A = DE1001855B
DE000001001650B = DE1001650B


# 1960:
DE000001086436B= DE1086436B
DE000001086014A=DE1086014B
DE000001073687A=DE1073687B


# Fazit:

# DE+Nummer<1000000
# B: IPS: Hier muss eine Umsetzung B->C rein
# A: IPS: Hier muss eine Umsetzung A->C rein

# DE+Nummer>1000000
# A: IPS: Hier muss eine Umsetzung A->B rein

# 1961:
DE000001101695A = DE1101695B

# 1963:
DE000001151898A = DE1151898B

# 1965:
DE000001207548A = DE1207548B
DE000001403081A = DE1403081A1
DE000001467818A = DE1467818A1
DE000001416855A = DE1416855A1
# IPS funktioniert automatisch

# 1974:
DE000007309197U = DE7309197U
# IPS funktioniert

#DE000002363448A = DE2363448A1
# IPS funktioniert automatisch

#DE000001467818B = DE1467818B2
# IPS funktioniert automatisch

# 1974
#DE000002343572B

# 1975:
#DE000001250596C2
#DE000001250596B
#DE000001250596A


# Übergang?
# Ab 1975 Übergang zu A1 und B
# PC=DE  und PY=1975 und IC=A61G? und Pub=13.03.1975

# Ab DEXXXXXXXX ca. >2000000 keine einstelligen Kindcodes mehr

# 1978:
# April: Wechsel zwischen U und U1
# DE000007210072U1
# DE000007739494U
"""


def convert_text(text, tests):
    #print dir(text)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        if '=' in line:
            lval, rval = line.split('=')
            number = lval.strip()
            expected = rval.strip()
            if expected == 'None':
                expected = None
            tests[number] = expected

convert_text(german_kindcode_fixes, t)


t['US000000024087E']        = 'USRE24087E'
t['US000000044856E']        = 'USRE44856E'


# 2014-10-04: strip leading zeros (DEPATISnet yields numbers like JP002011251389A or JP00000S602468B2)
t['JP00000S602468B2']       = 'JPS602468B2'

# 2015-09-01: properly convert japanese numbers into "HEISEI (HEI, H) - reign of Emperor Akihito" format
t['JP01153210A']            = 'JPH01153210A'
t['JP01206674A']            = 'JPH01206674A'

# 2015-09-01: mogrify kindcodes for japanese edge cases, here: JP08007001AA => JPH087001A
t['JP08007001AA']           = 'JPH087001A'

# 2015-09-01: mogrify kindcodes for patents from sweden, here: SE9503964A => SE9503964L
t['SE9503964A']             = 'SE9503964L'

# 2017-10-25
# DEPATISnet started delivering application publication numbers in 5+7 format
# with a leading zero after the country, e.g. US000006166174A, US020170285092A1
# around October 2017. Account for that.
t['US020170285092A1']       = 'US2017285092A1'


test_numbers_normalized_ok = t


class TestNumberNormalization:

    def examples_ok(self):
        for number, number_normalized_expect in test_numbers_normalized_ok.iteritems():
            number_normalized_computed = normalize_patent(number, fix_kindcode=True, for_ops=True)
            yield number, number_normalized_expect, number_normalized_computed

    def testDecodeOK(self):
        for number, expected, computed in self.examples_ok():
            yield self.check_ok, number, expected, computed

    #def testDecodeFAIL(self):
    #    for ipc_class in test_ipc_classes_fail:
    #        yield self.check_fail, ipc_class

    def check_ok(self, number, expected, computed):
        assert computed == expected, "number: %s, expected: %s, computed: %s" % (number, expected, computed)

        #@nose.tools.raises(ValueError)
        #def check_fail(self, ipc_class):
        #    IpcDecoder(ipc_class['raw'])
