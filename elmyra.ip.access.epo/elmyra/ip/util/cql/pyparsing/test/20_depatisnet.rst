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

>>> from elmyra.ip.util.cql.pyparsing import CQL


Logic operators localized
=========================

Test some logic operators localized to german.

Getting started
---------------
>>> CQL('bi=(greifer oder bagger)').dumps()
u'bi=(greifer ODER bagger)'

Made up
-------
Try to understand the query.

>>> CQL('bi=((wasser UND Getränk) NICHT (?hahn oder ?zapf oder (kühl? oder ?kühl)))').dumps()
u'bi=((wasser UND Getr\xe4nk) NICHT (?hahn ODER ?zapf ODER (k\xfchl? ODER ?k\xfchl)))'

Extract keywords from query.

>>> CQL('bi=((wasser UND Getränk) NICHT (?hahn oder ?zapf oder (kühl? oder ?kühl)))').polish().keywords()
[u'wasser', u'Getr\xe4nk', u'hahn', u'zapf', u'k\xfchl', u'k\xfchl']


Neighbourhood operators
=======================

Getting started
---------------

Try a bareword query string containing a neighbourhood term operator:

>>> CQL('L(W)Serine').dumps()
u'L(W)Serine'

Try the same in the context of a real condition (triple):

>>> CQL('ab=(L(W)Serine)').dumps()
u'ab=(L(W)Serine)'

Check this works caseless as well:

>>> CQL('L(w)Serine').dumps()
u'L(W)Serine'


Made up
-------

Try some more complex queries containing neighbourhood term operators and wildcards.

>>> CQL('bi=(Cry1?(L)resist?)').dumps()
u'bi=(Cry1?(L)resist?)'

>>> CQL('bi=(Cry1?(5A)tox?)').dumps()
u'bi=(Cry1?(5A)tox?)'

>>> CQL('bi=(Misch?(P)?wasser)').dumps()
u'bi=(Misch?(P)?wasser)'



Examples from DEPATISnet help
=============================

see also:

- english: `DEPATISnet Expert mode guide`_
- german: `DEPATISnet Expertenrecherche Handbuch`_


Search examples
---------------

>>> CQL('PA= siemens').dumps()
u'PA=siemens'

>>> CQL('PUB= 01.03.2010 UND PA= siemens').dumps()
u'PUB=01.03.2010 UND PA=siemens'

>>> CQL('PA= siemens UND IN= Braun UND PUB>= 01.03.2010').dumps()
u'PA=siemens UND IN=Braun UND PUB >= 01.03.2010'

>>> CQL('PUB= M11-2009 UND PA= daimler?').dumps()
u'PUB=M11-2009 UND PA=daimler?'

>>> CQL('AB = !!!lösung').dumps()
u'AB=!!!l\xf6sung'

>>> CQL('TI = ###heizung').dumps()
u'TI=###heizung'

>>> CQL('CL = ?fahrzeug').dumps()
u'CL=?fahrzeug'

>>> CQL('BI= (programmabschnitt# UND administra?)').dumps()
u'BI=(programmabschnitt# UND administra?)'


>>> CQL('ICB=F17D5/00').dumps()
u'ICB=F17D5/00'

>>> CQL('ICB=F17D5-00').dumps()
u'ICB=F17D5-00'

>>> CQL("ICB='F17D 5/00'").dumps()
u"ICB='F17D 5/00'"

>>> CQL('ICB=F17D0005000000').dumps()
u'ICB=F17D0005000000'


>>> CQL('ICP=F17D5/00M').dumps()
u'ICP=F17D5/00M'

>>> CQL('ICP=F17D5-00M').dumps()
u'ICP=F17D5-00M'

>>> CQL("ICP='F17D 5/00 M'").dumps()
u"ICP='F17D 5/00 M'"

>>> CQL('ICP=F17D000500000M').dumps()
u'ICP=F17D000500000M'


>>> CQL('ICB=F04D13/?').dumps()
u'ICB=F04D13/?'

>>> CQL('ICB=F04D13-?').dumps()
u'ICB=F04D13-?'

>>> CQL("ICB='F04D 13/?'").dumps()
u"ICB='F04D 13/?'"

>>> CQL('ICB=F04D0013?').dumps()
u'ICB=F04D0013?'


Search examples for the proximity operator (NOTW)
-------------------------------------------------
>>> CQL('Bi= (Regler und (mechanische(NOTW)Regler))').dumps()
u'Bi=(Regler UND (mechanische(NOTW)Regler))'

>>> CQL('Bi= (Regler und (mechanische (NOTW) Regler))').dumps()
u'Bi=(Regler UND (mechanische (NOTW) Regler))'


Searches in the text fields "Title", "Abstract", "Description", "Claims", "Full text data"
------------------------------------------------------------------------------------------
>>> CQL('TI = ( DVB(W)T )').dumps()
u'TI=(DVB(W)T)'

>>> CQL('Bi= (personalcomputer oder (personal(W)computer))').dumps()
u'Bi=(personalcomputer ODER (personal(W)computer))'


Searches in the fields "Applicant/Owner", "Inventor"
----------------------------------------------------
>>> CQL('PA = ( Anna(L)Huber )').dumps()
u'PA=(Anna(L)Huber)'


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
u"(PA=siemens UND IN=Braun UND PUB >= 01.03.2010) or (PUB=M11-2009 UND PA=daimler?) or (AB=(!!!l\xf6sung or ###heizung or ?fahrzeug)) or (ICB='F17D 5/00' or ICB=F04D13-?) or bi=(mechanische (NOTW) Regler) or bi=(Cry1?(L)resist? or Cry1?(5A)tox? or Misch?(P)?wasser)"

>>> CQL(largequery).keywords()
[u'siemens', u'Braun', u'daimler', [u'mechanische', u'Regler']]


Polishing
=========

Polishing a query, especially the shortcut notation expansion, should not corrupt query syntax.

>>> CQL('TI = ( DVB(W)T )').polish().dumps()
u'TI=(DVB(W)T)'

>>> CQL('Bi= (personalcomputer oder (personal(W)computer))').polish().dumps()
u'(Bi=personalcomputer ODER (Bi=(personal(W)computer)))'

>>> CQL('bi=(Cry1?(L)resist?)').polish().dumps()
u'bi=(Cry1?(L)resist?)'


>>> CQL(largequery).polish().dumps()
u"(PA=siemens UND IN=Braun UND PUB >= 01.03.2010) or (PUB=M11-2009 UND PA=daimler?) or ((AB=!!!l\xf6sung or AB=###heizung or AB=?fahrzeug)) or (ICB='F17D 5/00' or ICB=F04D13-?) or bi=(mechanische (NOTW) Regler) or (bi=(Cry1?(L)resist?) or bi=(Cry1?(5A)tox?) or bi=(Misch?(P)?wasser))"

>>> CQL(largequery).polish().keywords()
[u'siemens', u'Braun', u'daimler', u'l\xf6sung', u'heizung', u'fahrzeug', [u'mechanische', u'Regler'], [u'Cry1', u'resist'], [u'Cry1', u'tox'], [u'Misch', u'wasser']]


From the wild
=============

Some queries picked up from customers.

>>> CQL('bi=((warm(P)walzen) and (band(P)mitte and messung) or ((warm and walzen) and (band and säbel and messung)))').dumps()
u'bi=((warm(P)walzen) and (band(P)mitte and messung) or ((warm and walzen) and (band and s\xe4bel and messung)))'

>>> CQL('bi=((warm(P)walzen) and (band(P)mitte and messung) or ((warm and walzen) and (band and säbel and messung)))').polish().dumps()
u'((bi=(warm(P)walzen)) and (bi=(band(P)mitte) and bi=messung) or ((bi=warm and bi=walzen) and (bi=band and bi=s\xe4bel and bi=messung)))'

>>> CQL('bi=((warm(P)walzen) and (band(P)mitte and messung) or ((warm and walzen) and (band and säbel and messung)))').polish().keywords()
[[u'warm', u'walzen'], [u'band', u'mitte'], u'messung', u'warm', u'walzen', u'band', u's\xe4bel', u'messung']
