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
'H01F7/00'

# Rewrite all patent classifications from IFI format to OPS format
>>> IFIClaimsParser('ic:G01F000184').parse().rewrite_classes_ops().dumps()
'ic : G01F1/84'

>>> IFIClaimsParser('ic:G01F000184').keywords
['G01F1/84']

>>> IFIClaimsExpression.pair_to_solr('class', 'H04L12/433 or H04L12/24')
{'query': '((ic:H04L0012433 OR cpc:H04L0012433) OR (ic:H04L001224 OR cpc:H04L001224))'}

>>> IFIClaimsExpression.pair_to_solr('class', 'H01F7/00 or (H01F7/02 and H02K7/1876)')
{'query': '((ic:H01F000700 OR cpc:H01F000700) OR ((ic:H01F000702 OR cpc:H01F000702) AND (ic:H02K00071876 OR cpc:H02K00071876)))'}

>>> IFIClaimsExpression.pair_to_solr('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')
{'query': '((ic:H01F000700 OR cpc:H01F000700) NOT ((ic:H01F000702 OR cpc:H01F000702) OR (ic:H02K00071876 OR cpc:H02K00071876)))'}


Publication date
================

>>> IFIClaimsExpression.pair_to_solr('pubdate', 'foobar')
{'error': True, 'message': 'IFI CLAIMS query: Invalid date or range expression "foobar". Reason: foobar.'}


*********
Full text
*********

Simple expressions
==================

>>> IFIClaimsParser('ttl:bildschirm').keywords
['bildschirm']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm')
{'query': 'text:bildschirm'}


>>> IFIClaimsParser('ttl:bildschirm or ab:fahrzeug').keywords
['bildschirm', 'fahrzeug']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm or fahrzeug')
{'query': 'text:(bildschirm OR fahrzeug)'}


>>> IFIClaimsParser('ttl:bildschirm and ab:(fahrzeug or pkw)').keywords
['bildschirm', 'fahrzeug', 'pkw']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm and (fahrzeug or pkw)')
{'query': 'text:(bildschirm AND (fahrzeug OR pkw))'}


>>> IFIClaimsParser('ttl:bildschirm and ab:(fahrzeug or pkw not lkw)').keywords
['bildschirm', 'fahrzeug', 'pkw', 'lkw']

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm and (fahrzeug or pkw not lkw)')
{'query': 'text:(bildschirm AND (fahrzeug OR pkw NOT lkw))'}


>>> IFIClaimsParser('ab:fahrzeug or ab:pkw').keywords
['fahrzeug', 'pkw']


>>> IFIClaimsParser('ab:fahrzeug not ttl:pkw').keywords
['fahrzeug', 'pkw']



Expressions with proximity operators
====================================

Queries based on the proximity of words to each other in a document.

>>> IFIClaimsParser('text:((aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*))').keywords
['aussto', 'eject', 'pusher', 'verriegel', 'lock', 'sperr']

>>> IFIClaimsParser('{!complexphrase}text:"(aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*)"~6').keywords
['aussto', 'eject', 'pusher', 'verriegel', 'lock', 'sperr']

>>> IFIClaimsExpression.pair_to_solr('fulltext', '{!complexphrase}text:"(aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*)"~6')
{'query': '{!complexphrase}text:"(aussto* OR eject* OR pusher*) AND (verriegel* OR lock* OR sperr*)"~6'}

>>> IFIClaimsParser('{!complexphrase}text:"parallel* AND schalt*"~6 AND ((ic:F16H006104 OR cpc:F16H006104))').keywords
['parallel', 'schalt', 'F16H61/04']

>>> IFIClaimsParser('((ic:F16H006104 OR cpc:F16H006104)) AND {!complexphrase}text:"parallel* AND schalt*"~6').keywords
['F16H61/04', 'parallel', 'schalt']

>>> IFIClaimsParser('{!complexphrase}text:("parallel* AND schalt*"~6 AND "antrieb* AND stufe*"~3)').keywords
['parallel', 'schalt', 'antrieb', 'stufe']



Expressions without qualifying fieldnames
=========================================

Queries without proper fieldnames like ab=, ti=, bi=, etc. on the left side of the term.


>>> IFIClaimsParser('bildschirm').dumps()
'bildschirm'

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm')
{'query': 'text:bildschirm'}


>>> IFIClaimsParser('bildschirm and fahrzeug').dumps()
'bildschirm and fahrzeug'

>>> IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm and fahrzeug')
{'query': 'text:(bildschirm AND fahrzeug)'}



Expressions containing quoted words
===================================

>>> IFIClaimsParser('"bildschirm"').dumps()
'"bildschirm"'

>>> IFIClaimsParser('"bildschirm"').keywords
[]

>>> IFIClaimsExpression.pair_to_solr('fulltext', '"bildschirm"')
{'query': 'text:"bildschirm"'}

>>> IFIClaimsParser('ab:"bildschirm"').dumps()
'ab : "bildschirm"'

>>> IFIClaimsParser('ab:"bildschirm"').keywords
['bildschirm']

>>> IFIClaimsParser('text:(("aussto*" OR "eject*" OR pusher*) AND (verriegel* OR lock* OR sperr*))').keywords
['aussto', 'eject', 'pusher', 'verriegel', 'lock', 'sperr']



Keyword extraction
==================

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('class', 'H01F7/00')['query']).keywords
['H01F7/00']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')['query']).keywords
['H01F7/00', 'H01F7/02', 'H02K7/1876']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('fulltext', 'bildschirm')['query']).keywords
['bildschirm']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('fulltext', '"bildschirm"')['query']).keywords
['bildschirm']

>>> IFIClaimsParser(IFIClaimsExpression.pair_to_solr('fulltext', 'ttl:bildschirm OR ab:(fahrzeug OR pkw)')['query']).keywords
['bildschirm', 'fahrzeug', 'pkw']



From the wild
=============

Umlauts
-------

>>> IFIClaimsParser('tac:((*messschieber* OR *meßschieber*) AND *digital* )').dumps()
'((tac : *messschieber* or tac : *me\xdfschieber*) and tac : *digital*)'

>>> IFIClaimsParser('tac:((*messschieber* OR *meßschieber*) AND *digital* )').keywords
['messschieber', 'me\xdfschieber', 'digital']


More
----

>>> IFIClaimsParser('ttl:(energy and water) or ab:(waves or Tide) and clm:"90°"').keywords
['energy', 'water', 'waves', 'Tide', '90\xb0']

>>> IFIClaimsParser('text:(((bremsgefühl* or pedalgefühl) and (*simulator or simul*)) and (separ* or getrennt* or entkoppel* or entkoppl* or decoupl*) and (eigenständig* or independent* or autonom*))').keywords
['bremsgef\xfchl', 'pedalgef\xfchl', 'simulator', 'simul', 'separ', 'getrennt', 'entkoppel', 'entkoppl', 'decoupl', 'eigenst\xe4ndig', 'independent', 'autonom']
