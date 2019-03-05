.. -*- coding: utf-8 -*-
.. (c) 2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

==================================
IFI CLAIMS expression parser tests
==================================

>>> from patzilla.access.ificlaims.expression import IFIClaimsParser, IFIClaimsExpression


******************
Bibliographic data
******************

Empty query
===========
>>> IFIClaimsParser('').dumps()
''

IPC/CPC
=======
>>> IFIClaimsParser('H01F7/00').dumps()
u'H01F7/00'

# Rewrite all patent classifications from IFI format to OPS format
>>> IFIClaimsParser('ic:G01F000184').parse().rewrite_classes_ops().dumps()
u'ic : G01F1/84'

>>> IFIClaimsParser('ic:G01F000184').keywords
[u'G01F1/84']

>>> IFIClaimsExpression.pair_to_solr('class', 'H04L12/433 or H04L12/24')
{'query': u'((ic:H04L0012433 OR cpc:H04L0012433) OR (ic:H04L001224 OR cpc:H04L001224))'}

>>> IFIClaimsExpression.pair_to_solr('class', 'H01F7/00 or (H01F7/02 and H02K7/1876)')
{'query': u'((ic:H01F000700 OR cpc:H01F000700) OR ((ic:H01F000702 OR cpc:H01F000702) AND (ic:H02K00071876 OR cpc:H02K00071876)))'}

>>> IFIClaimsExpression.pair_to_solr('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')
{'query': u'((ic:H01F000700 OR cpc:H01F000700) NOT ((ic:H01F000702 OR cpc:H01F000702) OR (ic:H02K00071876 OR cpc:H02K00071876)))'}


Publication date
================

>>> IFIClaimsExpression.pair_to_solr('pubdate', 'foobar')
{'message': 'IFI CLAIMS query: Invalid date or range expression "foobar". Reason: foobar.', 'error': True}


*********
Full text
*********

Simple expressions
==================

>>> IFIClaimsParser('ttl:bildschirm').keywords
[u'bildschirm']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm')
{'query': u'text:bildschirm'}


>>> IFIClaimsParser('ttl:bildschirm or ab:fahrzeug').keywords
[u'bildschirm', u'fahrzeug']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm or fahrzeug')
{'query': u'text:(bildschirm OR fahrzeug)'}


>>> IFIClaimsParser('ttl:bildschirm and ab:(fahrzeug or pkw)').keywords
[u'bildschirm', u'fahrzeug', u'pkw']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm and (fahrzeug or pkw)')
{'query': u'text:(bildschirm AND (fahrzeug OR pkw))'}


>>> IFIClaimsParser('ttl:bildschirm and ab:(fahrzeug or pkw not lkw)').keywords
[u'bildschirm', u'fahrzeug', u'pkw', u'lkw']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm and (fahrzeug or pkw not lkw)')
{'query': u'text:(bildschirm AND (fahrzeug OR pkw NOT lkw))'}


>>> IFIClaimsParser('ab:fahrzeug or ab:pkw').keywords
[u'fahrzeug', u'pkw']


>>> IFIClaimsParser('ab:fahrzeug not ttl:pkw').keywords
[u'fahrzeug', u'pkw']



Expressions with proximity operators
====================================

Queries based on the proximity of words to each other in a document.

>>> IFIClaimsParser('text:((aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*))').keywords
[u'aussto', u'eject', u'pusher', u'verriegel', u'lock', u'sperr']

>>> IFIClaimsParser('{!complexphrase}text:"(aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*)"~6').keywords
[u'aussto', u'eject', u'pusher', u'verriegel', u'lock', u'sperr']

>>> IFIClaimsExpression.pair_to_solr('fulltext', '{!complexphrase}text:"(aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*)"~6')
{'query': '{!complexphrase}text:"(aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*)"~6'}

>>> IFIClaimsParser('{!complexphrase}text:"parallel* AND schalt*"~6 AND ((ic:F16H006104 OR cpc:F16H006104))').keywords
[u'parallel', u'schalt', u'F16H61/04']

>>> IFIClaimsParser('((ic:F16H006104 OR cpc:F16H006104)) AND {!complexphrase}text:"parallel* AND schalt*"~6').keywords
[u'F16H61/04', u'parallel', u'schalt']

>>> IFIClaimsParser('{!complexphrase}text:("parallel* AND schalt*"~6 AND "antrieb* AND stufe*"~3)').keywords
[u'parallel', u'schalt', u'antrieb', u'stufe']



Expressions without qualifying fieldnames
=========================================

Queries without proper fieldnames like ab=, ti=, bi=, etc. on the left side of the term.


>>> IFIClaimsParser('bildschirm').dumps()
u'bildschirm'

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm')
{'query': u'text:bildschirm'}


>>> IFIClaimsParser('bildschirm and fahrzeug').dumps()
u'bildschirm and fahrzeug'

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm and fahrzeug')
{'query': u'text:(bildschirm AND fahrzeug)'}



Expressions containing quoted words
===================================

>>> IFIClaimsParser('"bildschirm"').dumps()
u'"bildschirm"'

>>> IFIClaimsParser('"bildschirm"').keywords
[]

>>> IFIClaimsExpression.pair_to_solr('fulltext', '"bildschirm"')
{'query': u'text:"bildschirm"'}

>>> IFIClaimsParser('ab:"bildschirm"').dumps()
u'ab : "bildschirm"'

>>> IFIClaimsParser('ab:"bildschirm"').keywords
[u'bildschirm']

>>> IFIClaimsParser('text:(("aussto*" OR "eject*" OR pusher*) AND (verriegel* OR lock* OR sperr*))').keywords
[u'aussto', u'eject', u'pusher', u'verriegel', u'lock', u'sperr']



Keyword extraction
==================

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('class', 'H01F7/00')['query']).keywords
[u'H01F7/00']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')['query']).keywords
[u'H01F7/00', u'H01F7/02', u'H02K7/1876']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm')['query']).keywords
[u'bildschirm']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('fulltext', '"bildschirm"')['query']).keywords
[u'bildschirm']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('fulltext', 'ttl:bildschirm OR ab:(fahrzeug OR pkw)')['query']).keywords
[u'bildschirm', u'fahrzeug', u'pkw']



From the wild
=============

Umlauts
-------

>>> IFIClaimsParser(u'tac:((*messschieber* OR *meßschieber*) AND *digital* )').dumps()
u'((tac : *messschieber* or tac : *me\xdfschieber*) and tac : *digital*)'

>>> IFIClaimsParser(u'tac:((*messschieber* OR *meßschieber*) AND *digital* )').keywords
[u'messschieber', u'me\xdfschieber', u'digital']


More
----

>>> IFIClaimsParser(u'ttl:(energy and water) or ab:(waves or Tide) and clm:"90°"').keywords
[u'energy', u'water', u'waves', u'Tide', u'90\xb0']

>>> IFIClaimsParser(u'text:(((bremsgefühl* or pedalgefühl) and (*simulator or simul*)) and (separ* or getrennt* or entkoppel* or entkoppl* or decoupl*) and (eigenständig* or independent* or autonom*))').keywords
[u'bremsgef\xfchl', u'pedalgef\xfchl', u'simulator', u'simul', u'separ', u'getrennt', u'entkoppel', u'entkoppl', u'decoupl', u'eigenst\xe4ndig', u'independent', u'autonom']
