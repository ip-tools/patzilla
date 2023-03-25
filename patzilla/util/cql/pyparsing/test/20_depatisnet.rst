.. -*- coding: utf-8 -*-
.. (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

===============================================
CQL pyparsing parser tests: DEPATISnet features
===============================================

see also:

- english: `DEPATISnet Expert mode guide`_
- german: `DEPATISnet Expertenrecherche Handbuch`_

.. _DEPATISnet Expert mode guide: https://depatisnet.dpma.de/depatisnet/htdocs/prod/en/hilfe/recherchemodi/experten-recherche/
.. _DEPATISnet Expertenrecherche Handbuch: https://depatisnet.dpma.de/depatisnet/htdocs/prod/de/hilfe/recherchemodi/experten-recherche/

>>> from patzilla.access.dpma.depatisnet import DpmaDepatisnetAccess
>>> def CQL(expression):
...     from patzilla.util.cql.pyparsing import CQL as UpstreamCQL
...     return UpstreamCQL(expression, keyword_fields=DpmaDepatisnetAccess.keyword_fields)


Logic operators localized
=========================

Test some logic operators localized to german.

Getting started
---------------
>>> CQL('bi=(greifer oder bagger)').dumps()
'bi=(greifer ODER bagger)'

Made up
-------
Try to understand the query.

>>> CQL('bi=((wasser UND Getränk) NICHT (?hahn oder ?zapf oder (kühl? oder ?kühl)))').dumps()
'bi=((wasser UND Getr\xe4nk) NICHT (?hahn ODER ?zapf ODER (k\xfchl? ODER ?k\xfchl)))'

Extract keywords from query.

>>> CQL('bi=((wasser UND Getränk) NICHT (?hahn oder ?zapf oder (kühl? oder ?kühl)))').polish().keywords()
['wasser', 'Getr\xe4nk', 'hahn', 'zapf', 'k\xfchl', 'k\xfchl']


Neighbourhood operators
=======================

Getting started
---------------

Try a bareword query string containing a neighbourhood term operator:

>>> CQL('L(W)Serine').dumps()
'L(W)Serine'

Try the same in the context of a real condition (triple):

>>> CQL('ab=(L(W)Serine)').dumps()
'ab=(L(W)Serine)'

Check this works caseless as well:

>>> CQL('L(w)Serine').dumps()
'L(W)Serine'


Made up
-------

Try some more complex queries containing neighbourhood term operators and wildcards.

>>> CQL('bi=(Cry1?(L)resist?)').dumps()
'bi=(Cry1?(L)resist?)'

>>> CQL('bi=(Cry1?(5A)tox?)').dumps()
'bi=(Cry1?(5A)tox?)'

>>> CQL('bi=(Misch?(P)?wasser)').dumps()
'bi=(Misch?(P)?wasser)'



Examples from DEPATISnet help
=============================

see also:

- english: `DEPATISnet Expert mode guide`_
- german: `DEPATISnet Expertenrecherche Handbuch`_


Search examples
---------------

>>> CQL('PA= siemens').dumps()
'PA=siemens'

>>> CQL('PUB= 01.03.2010 UND PA= siemens').dumps()
'PUB=01.03.2010 UND PA=siemens'

>>> CQL('PA= siemens UND IN= Braun UND PUB>= 01.03.2010').dumps()
'PA=siemens UND IN=Braun UND PUB >= 01.03.2010'

>>> CQL('PUB= M11-2009 UND PA= daimler?').dumps()
'PUB=M11-2009 UND PA=daimler?'

>>> CQL('AB = !!!lösung').dumps()
'AB=!!!l\xf6sung'

>>> CQL('TI = ###heizung').dumps()
'TI=###heizung'

>>> CQL('CL = ?fahrzeug').dumps()
'CL=?fahrzeug'

>>> CQL('BI= (programmabschnitt# UND administra?)').dumps()
'BI=(programmabschnitt# UND administra?)'


>>> CQL('ICB=F17D5/00').dumps()
'ICB=F17D5/00'

>>> CQL('ICB=F17D5-00').dumps()
'ICB=F17D5-00'

>>> CQL("ICB='F17D 5/00'").dumps()
"ICB='F17D 5/00'"

>>> CQL('ICB=F17D0005000000').dumps()
'ICB=F17D0005000000'


>>> CQL('ICP=F17D5/00M').dumps()
'ICP=F17D5/00M'

>>> CQL('ICP=F17D5-00M').dumps()
'ICP=F17D5-00M'

>>> CQL("ICP='F17D 5/00 M'").dumps()
"ICP='F17D 5/00 M'"

>>> CQL('ICP=F17D000500000M').dumps()
'ICP=F17D000500000M'


>>> CQL('ICB=F04D13/?').dumps()
'ICB=F04D13/?'

>>> CQL('ICB=F04D13-?').dumps()
'ICB=F04D13-?'

>>> CQL("ICB='F04D 13/?'").dumps()
"ICB='F04D 13/?'"

>>> CQL('ICB=F04D0013?').dumps()
'ICB=F04D0013?'


Search examples for the proximity operator (NOTW)
-------------------------------------------------
>>> CQL('Bi= (Regler und (mechanische(NOTW)Regler))').dumps()
'Bi=(Regler UND (mechanische(NOTW)Regler))'

>>> CQL('Bi= (Regler und (mechanische (NOTW) Regler))').dumps()
'Bi=(Regler UND (mechanische (NOTW) Regler))'


Searches in the text fields "Title", "Abstract", "Description", "Claims", "Full text data"
------------------------------------------------------------------------------------------
>>> CQL('TI = ( DVB(W)T )').dumps()
'TI=(DVB(W)T)'

>>> CQL('Bi= (personalcomputer oder (personal(W)computer))').dumps()
'Bi=(personalcomputer ODER (personal(W)computer))'


Searches in the fields "Applicant/owner", "Inventor"
----------------------------------------------------
>>> CQL('PA = ( Anna(L)Huber )').dumps()
'PA=(Anna(L)Huber)'


Keywords
========

Try some more complex queries containing *value shortcut notations*, *neighbourhood term operators* and *wildcards*.

>>> largequery = """
...     (PA= siemens UND IN= Braun UND PUB>= 01.03.2010) or
...     (PUB=M11-2009 UND PA=daimler?) or
...     (AB = (!!!lösung or ###heizung or ?fahrzeug)) or
...     (ICB='F17D 5/00' or ICB=F04D13-?) or
...     bi=(mechanische (NOTW) Regler) or
...     bi=(Cry1?(L)resist? or Cry1?(5A)tox? or Misch?(P)?wasser)
... """

>>> CQL(largequery).dumps()
"(PA=siemens UND IN=Braun UND PUB >= 01.03.2010) or (PUB=M11-2009 UND PA=daimler?) or (AB=(!!!l\xf6sung or ###heizung or ?fahrzeug)) or (ICB='F17D 5/00' or ICB=F04D13-?) or bi=(mechanische (NOTW) Regler) or bi=(Cry1?(L)resist? or Cry1?(5A)tox? or Misch?(P)?wasser)"

>>> CQL(largequery).keywords()
['siemens', 'Braun', 'daimler', 'F17D 5/00', 'F04D13-', ['mechanische', 'Regler']]


Polishing
=========

Polishing a query, especially the shortcut notation expansion, should not corrupt query syntax.

>>> CQL('TI = ( DVB(W)T )').polish().dumps()
'TI=(DVB(W)T)'

>>> CQL('Bi= (personalcomputer oder (personal(W)computer))').polish().dumps()
'(Bi=personalcomputer ODER (Bi=(personal(W)computer)))'

>>> CQL('bi=(Cry1?(L)resist?)').polish().dumps()
'bi=(Cry1?(L)resist?)'


>>> CQL(largequery).polish().dumps()
"(PA=siemens UND IN=Braun UND PUB >= 01.03.2010) or (PUB=M11-2009 UND PA=daimler?) or ((AB=!!!l\xf6sung or AB=###heizung or AB=?fahrzeug)) or (ICB='F17D 5/00' or ICB=F04D13-?) or bi=(mechanische (NOTW) Regler) or (bi=(Cry1?(L)resist?) or bi=(Cry1?(5A)tox?) or bi=(Misch?(P)?wasser))"

>>> CQL(largequery).polish().keywords()
['siemens', 'Braun', 'daimler', 'l\xf6sung', 'heizung', 'fahrzeug', 'F17D 5/00', 'F04D13-', ['mechanische', 'Regler'], ['Cry1', 'resist'], ['Cry1', 'tox'], ['Misch', 'wasser']]


From the wild
=============

Some queries picked up from customers.

Query 1
-------

Reproduce verbatim:

>>> print(CQL('(ab=radaufstandskraft or ab=radaufstandskräfte?)').dumps())
(ab=radaufstandskraft or ab=radaufstandskräfte?)

Reproduce with polishing:

>>> print(CQL('(ab=radaufstandskraft or ab=radaufstandskräfte?)').polish().dumps())
(ab=radaufstandskraft or ab=radaufstandskräfte?)

Extract keywords after polishing:

>>> CQL('(ab=radaufstandskraft or ab=radaufstandskräfte?)').polish().keywords()
['radaufstandskraft', 'radaufstandskr\xe4fte']


Query 2
-------

Reproduce verbatim:

>>> print(CQL('bi=( ( warm(P)walzen)  AND ( band(P)mitte and messung) )  oder  bi=( ( warm  and walzen)  AND ( band and säbel and messung) ) oder bi=((warm and walzen)and (mitten und messung)) oder  BI =((reversiergerüst)und(breitenmessung))').dumps())
bi=((warm(P)walzen) and (band(P)mitte and messung)) ODER bi=((warm and walzen) and (band and säbel and messung)) ODER bi=((warm and walzen) and (mitten UND messung)) ODER BI=((reversiergerüst) UND (breitenmessung))

Reproduce with polishing:

>>> print(CQL('bi=( ( warm(P)walzen)  AND ( band(P)mitte and messung) )  oder  bi=( ( warm  and walzen)  AND ( band and säbel and messung) ) oder bi=((warm and walzen)and (mitten und messung)) oder  BI =((reversiergerüst)und(breitenmessung))').polish().dumps())
((bi=(warm(P)walzen)) and (bi=(band(P)mitte) and bi=messung)) ODER ((bi=warm and bi=walzen) and (bi=band and bi=säbel and bi=messung)) ODER ((bi=warm and bi=walzen) and (bi=mitten UND bi=messung)) ODER ((BI=reversiergerüst) UND (BI=breitenmessung))

Extract keywords after polishing:

>>> CQL('bi=( ( warm(P)walzen)  AND ( band(P)mitte and messung) )  oder  bi=( ( warm  and walzen)  AND ( band and säbel and messung) ) oder bi=((warm and walzen)and (mitten und messung)) oder  BI =((reversiergerüst)und(breitenmessung))').polish().keywords()
[['warm', 'walzen'], ['band', 'mitte'], 'messung', 'warm', 'walzen', 'band', 's\xe4bel', 'messung', 'warm', 'walzen', 'mitten', 'messung', 'reversierger\xfcst', 'breitenmessung']


Query 3
-------

Reproduce verbatim:

>>> print(CQL('bi=( ( hot(P)rolling)  AND ( strip(P)center and measurement)  oder ( hot  and rolling)  AND ( strip and camber and measurement) ) oder bi=((reversing and mill)and (camber)) ODER bi=( ( hot  and steel)  AND (center and measurement) )  ODER BI =((hot(P)slab) und(position(P)measurement)) ODER BI =((hot(P)strip) und(position(P)measurement))').dumps())
bi=((hot(P)rolling) and (strip(P)center and measurement) ODER (hot and rolling) and (strip and camber and measurement)) ODER bi=((reversing and mill) and (camber)) ODER bi=((hot and steel) and (center and measurement)) ODER BI=((hot(P)slab) UND (position(P)measurement)) ODER BI=((hot(P)strip) UND (position(P)measurement))

Reproduce with polishing:

>>> print(CQL('bi=( ( hot(P)rolling)  AND ( strip(P)center and measurement)  oder ( hot  and rolling)  AND ( strip and camber and measurement) ) oder bi=((reversing and mill)and (camber)) ODER bi=( ( hot  and steel)  AND (center and measurement) )  ODER BI =((hot(P)slab) und(position(P)measurement)) ODER BI =((hot(P)strip) und(position(P)measurement))').polish().dumps())
((bi=(hot(P)rolling)) and (bi=(strip(P)center) and bi=measurement) ODER (bi=hot and bi=rolling) and (bi=strip and bi=camber and bi=measurement)) ODER ((bi=reversing and bi=mill) and (bi=camber)) ODER ((bi=hot and bi=steel) and (bi=center and bi=measurement)) ODER ((BI=(hot(P)slab)) UND (BI=(position(P)measurement))) ODER ((BI=(hot(P)strip)) UND (BI=(position(P)measurement)))

Extract keywords after polishing:

>>> CQL('bi=( ( hot(P)rolling)  AND ( strip(P)center and measurement)  oder ( hot  and rolling)  AND ( strip and camber and measurement) ) oder bi=((reversing and mill)and (camber)) ODER bi=( ( hot  and steel)  AND (center and measurement) )  ODER BI =((hot(P)slab) und(position(P)measurement)) ODER BI =((hot(P)strip) und(position(P)measurement))').polish().keywords()
[['hot', 'rolling'], ['strip', 'center'], 'measurement', 'hot', 'rolling', 'strip', 'camber', 'measurement', 'reversing', 'mill', 'camber', 'hot', 'steel', 'center', 'measurement', ['hot', 'slab'], ['position', 'measurement'], ['hot', 'strip'], ['position', 'measurement']]


Query 4
-------

Reproduce verbatim:

>>> print(CQL('BI=((finne? or (flying(1a)buttress?) or fins or effillee?) and (viergelenk? or mehrgelenk? or quadrilateral? or quadruple? or (four(w)joint) or quadrilaterale or quatre))').dumps())
BI=((finne? or (flying(1A)buttress?) or fins or effillee?) and (viergelenk? or mehrgelenk? or quadrilateral? or quadruple? or (four(W)joint) or quadrilaterale or quatre))

Reproduce with polishing:

>>> print(CQL('BI=((finne? or (flying(1a)buttress?) or fins or effillee?) and (viergelenk? or mehrgelenk? or quadrilateral? or quadruple? or (four(w)joint) or quadrilaterale or quatre))').polish().dumps())
((BI=finne? or (BI=(flying(1A)buttress?)) or BI=fins or BI=effillee?) and (BI=viergelenk? or BI=mehrgelenk? or BI=quadrilateral? or BI=quadruple? or (BI=(four(W)joint)) or BI=quadrilaterale or BI=quatre))

Extract keywords after polishing:

>>> CQL('BI=((finne? or (flying(1a)buttress?) or fins or effillee?) and (viergelenk? or mehrgelenk? or quadrilateral? or quadruple? or (four(w)joint) or quadrilaterale or quatre))').polish().keywords()
['finne', ['flying', 'buttress'], 'fins', 'effillee', 'viergelenk', 'mehrgelenk', 'quadrilateral', 'quadruple', ['four', 'joint'], 'quadrilaterale', 'quatre']
