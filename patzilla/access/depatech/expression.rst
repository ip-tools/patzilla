.. -*- coding: utf-8 -*-
.. (c) 2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

=================================
depa.tech expression parser tests
=================================

>>> from patzilla.access.depatech.expression import DepaTechParser, DepaTechExpression


******************
Bibliographic data
******************

Empty query
===========
>>> DepaTechParser('').dumps()
''

IPC/CPC
=======
>>> DepaTechParser('H01F7/00').dumps()
u'H01F7/00'

# Rewrite all patent classifications from depa.tech format to OPS format
>>> DepaTechParser('IC:G01F000184').parse().rewrite_classes_ops().dumps()
u'IC : G01F1/84'

>>> DepaTechParser('IC:G01F000184').keywords
[u'G01F1/84']

>>> DepaTechExpression.pair_to_elasticsearch('class', 'H04L12/433 or H04L12/24')
{'query': u'((IC:H04L0012433 OR NC:H04L0012433) OR (IC:H04L001224 OR NC:H04L001224))'}

>>> DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00 or (H01F7/02 and H02K7/1876)')
{'query': u'((IC:H01F000700 OR NC:H01F000700) OR ((IC:H01F000702 OR NC:H01F000702) AND (IC:H02K00071876 OR NC:H02K00071876)))'}

>>> DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')
{'query': u'((IC:H01F000700 OR NC:H01F000700) NOT ((IC:H01F000702 OR NC:H01F000702) OR (IC:H02K00071876 OR NC:H02K00071876)))'}


Publication date
================

>>> DepaTechExpression.pair_to_elasticsearch('pubdate', 'foobar')
{'message': 'depatech query: Invalid date or range expression "foobar". Reason: foobar.', 'error': True}


*********
Full text
*********

Simple expressions
==================

>>> DepaTechParser('GT:bildschirm').keywords
[u'bildschirm']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm')
{'query': u'(AB:bildschirm OR GT:bildschirm OR ET:bildschirm OR FT:bildschirm)'}


>>> DepaTechParser('GT:bildschirm or AB:fahrzeug').keywords
[u'bildschirm', u'fahrzeug']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm or fahrzeug')
{'query': u'(AB:(bildschirm OR fahrzeug) OR GT:(bildschirm OR fahrzeug) OR ET:(bildschirm OR fahrzeug) OR FT:(bildschirm OR fahrzeug))'}


>>> DepaTechParser('GT:bildschirm and AB:(fahrzeug or pkw)').keywords
[u'bildschirm', u'fahrzeug', u'pkw']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm and (fahrzeug or pkw)')
{'query': u'(AB:(bildschirm AND (fahrzeug OR pkw)) OR GT:(bildschirm AND (fahrzeug OR pkw)) OR ET:(bildschirm AND (fahrzeug OR pkw)) OR FT:(bildschirm AND (fahrzeug OR pkw)))'}


>>> DepaTechParser('GT:bildschirm and AB:(fahrzeug or pkw not lkw)').keywords
[u'bildschirm', u'fahrzeug', u'pkw', u'lkw']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm and (fahrzeug or pkw not lkw)')
{'query': u'(AB:(bildschirm AND (fahrzeug OR pkw NOT lkw)) OR GT:(bildschirm AND (fahrzeug OR pkw NOT lkw)) OR ET:(bildschirm AND (fahrzeug OR pkw NOT lkw)) OR FT:(bildschirm AND (fahrzeug OR pkw NOT lkw)))'}


>>> DepaTechParser('AB:fahrzeug or AB:pkw').keywords
[u'fahrzeug', u'pkw']


>>> DepaTechParser('AB:fahrzeug not GT:pkw').keywords
[u'fahrzeug', u'pkw']



Expressions without qualifying fieldnames
=========================================

Queries without proper fieldnames like AB:, GT:, AB:, etc. on the left side of the term.


>>> DepaTechParser('bildschirm').dumps()
u'bildschirm'

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm')
{'query': u'(AB:bildschirm OR GT:bildschirm OR ET:bildschirm OR FT:bildschirm)'}


>>> DepaTechParser('bildschirm and fahrzeug').dumps()
u'bildschirm and fahrzeug'

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm and fahrzeug')
{'query': u'(AB:(bildschirm AND fahrzeug) OR GT:(bildschirm AND fahrzeug) OR ET:(bildschirm AND fahrzeug) OR FT:(bildschirm AND fahrzeug))'}



Expressions containing quoted words
===================================

>>> DepaTechParser('"bildschirm"').dumps()
u'"bildschirm"'

>>> DepaTechParser('"bildschirm"').keywords
[]

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', '"bildschirm"')
{'query': u'(AB:"bildschirm" OR GT:"bildschirm" OR ET:"bildschirm" OR FT:"bildschirm")'}

>>> DepaTechParser('AB:"bildschirm"').dumps()
u'AB : "bildschirm"'

>>> DepaTechParser('AB:"bildschirm"').keywords
[u'bildschirm']

>>> DepaTechParser('AB:(("aussto*" OR "eject*" OR pusher*) AND (verriegel* OR lock* OR sperr*))').keywords
[u'aussto', u'eject', u'pusher', u'verriegel', u'lock', u'sperr']



Keyword extraction
==================

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00')['query']).keywords
[u'H01F7/00']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')['query']).keywords
[u'H01F7/00', u'H01F7/02', u'H02K7/1876']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm')['query']).keywords
[u'bildschirm']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('fulltext', '"bildschirm"')['query']).keywords
[u'bildschirm']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('fulltext', 'GT:bildschirm OR AB:(fahrzeug OR pkw)')['query']).keywords
[u'bildschirm', u'fahrzeug', u'pkw']



From the wild
=============

Umlauts
-------

>>> DepaTechParser(u'AB:((*messschieber* OR *meßschieber*) AND *digital* )').dumps()
u'((AB : *messschieber* or AB : *me\xdfschieber*) and AB : *digital*)'

>>> DepaTechParser(u'AB:((*messschieber* OR *meßschieber*) AND *digital* )').keywords
[u'messschieber', u'me\xdfschieber', u'digital']


More
----

>>> DepaTechParser(u'ET:(energy and water) or AB:(waves or Tide) and AB:"90°"').keywords
[u'energy', u'water', u'waves', u'Tide', u'90\xb0']

>>> DepaTechParser(u'AB:(((bremsgefühl* or pedalgefühl) and (*simulator or simul*)) and (separ* or getrennt* or entkoppel* or entkoppl* or decoupl*) and (eigenständig* or independent* or autonom*))').keywords
[u'bremsgef\xfchl', u'pedalgef\xfchl', u'simulator', u'simul', u'separ', u'getrennt', u'entkoppel', u'entkoppl', u'decoupl', u'eigenst\xe4ndig', u'independent', u'autonom']
