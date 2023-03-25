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
'H01F7/00'

# Rewrite all patent classifications from depa.tech format to OPS format
>>> DepaTechParser('IC:G01F000184').parse().rewrite_classes_ops().dumps()
'IC : G01F1/84'

>>> DepaTechParser('IC:G01F000184').keywords
['G01F1/84']

>>> DepaTechExpression.pair_to_elasticsearch('class', 'H04L12/433 or H04L12/24')
{'query': '((IC:H04L0012433 OR NC:H04L0012433) OR (IC:H04L001224 OR NC:H04L001224))'}

>>> DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00 or (H01F7/02 and H02K7/1876)')
{'query': '((IC:H01F000700 OR NC:H01F000700) OR ((IC:H01F000702 OR NC:H01F000702) AND (IC:H02K00071876 OR NC:H02K00071876)))'}

>>> DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')
{'query': '((IC:H01F000700 OR NC:H01F000700) NOT ((IC:H01F000702 OR NC:H01F000702) OR (IC:H02K00071876 OR NC:H02K00071876)))'}


Publication date
================

>>> DepaTechExpression.pair_to_elasticsearch('pubdate', 'foobar')
{'error': True, 'message': 'depatech query: Invalid date or range expression "foobar". Reason: foobar.'}


*********
Full text
*********

Simple expressions
==================

>>> DepaTechParser('GT:bildschirm').keywords
['bildschirm']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm')
{'query': '(AB:bildschirm OR GT:bildschirm OR ET:bildschirm OR FT:bildschirm)'}


>>> DepaTechParser('GT:bildschirm or AB:fahrzeug').keywords
['bildschirm', 'fahrzeug']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm or fahrzeug')
{'query': '(AB:(bildschirm OR fahrzeug) OR GT:(bildschirm OR fahrzeug) OR ET:(bildschirm OR fahrzeug) OR FT:(bildschirm OR fahrzeug))'}


>>> DepaTechParser('GT:bildschirm and AB:(fahrzeug or pkw)').keywords
['bildschirm', 'fahrzeug', 'pkw']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm and (fahrzeug or pkw)')
{'query': '(AB:(bildschirm AND (fahrzeug OR pkw)) OR GT:(bildschirm AND (fahrzeug OR pkw)) OR ET:(bildschirm AND (fahrzeug OR pkw)) OR FT:(bildschirm AND (fahrzeug OR pkw)))'}


>>> DepaTechParser('GT:bildschirm and AB:(fahrzeug or pkw not lkw)').keywords
['bildschirm', 'fahrzeug', 'pkw', 'lkw']

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm and (fahrzeug or pkw not lkw)')
{'query': '(AB:(bildschirm AND (fahrzeug OR pkw NOT lkw)) OR GT:(bildschirm AND (fahrzeug OR pkw NOT lkw)) OR ET:(bildschirm AND (fahrzeug OR pkw NOT lkw)) OR FT:(bildschirm AND (fahrzeug OR pkw NOT lkw)))'}


>>> DepaTechParser('AB:fahrzeug or AB:pkw').keywords
['fahrzeug', 'pkw']


>>> DepaTechParser('AB:fahrzeug not GT:pkw').keywords
['fahrzeug', 'pkw']



Expressions without qualifying fieldnames
=========================================

Queries without proper fieldnames like AB:, GT:, AB:, etc. on the left side of the term.


>>> DepaTechParser('bildschirm').dumps()
'bildschirm'

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm')
{'query': '(AB:bildschirm OR GT:bildschirm OR ET:bildschirm OR FT:bildschirm)'}


>>> DepaTechParser('bildschirm and fahrzeug').dumps()
'bildschirm and fahrzeug'

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm and fahrzeug')
{'query': '(AB:(bildschirm AND fahrzeug) OR GT:(bildschirm AND fahrzeug) OR ET:(bildschirm AND fahrzeug) OR FT:(bildschirm AND fahrzeug))'}



Expressions containing quoted words
===================================

>>> DepaTechParser('"bildschirm"').dumps()
'"bildschirm"'

>>> DepaTechParser('"bildschirm"').keywords
[]

>>> DepaTechExpression.pair_to_elasticsearch('fulltext', '"bildschirm"')
{'query': '(AB:"bildschirm" OR GT:"bildschirm" OR ET:"bildschirm" OR FT:"bildschirm")'}

>>> DepaTechParser('AB:"bildschirm"').dumps()
'AB : "bildschirm"'

>>> DepaTechParser('AB:"bildschirm"').keywords
['bildschirm']

>>> DepaTechParser('AB:(("aussto*" OR "eject*" OR pusher*) AND (verriegel* OR lock* OR sperr*))').keywords
['aussto', 'eject', 'pusher', 'verriegel', 'lock', 'sperr']



Keyword extraction
==================

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00')['query']).keywords
['H01F7/00']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('class', 'H01F7/00 not (H01F7/02 or H02K7/1876)')['query']).keywords
['H01F7/00', 'H01F7/02', 'H02K7/1876']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('fulltext', 'bildschirm')['query']).keywords
['bildschirm']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('fulltext', '"bildschirm"')['query']).keywords
['bildschirm']

>>> DepaTechParser(DepaTechExpression.pair_to_elasticsearch('fulltext', 'GT:bildschirm OR AB:(fahrzeug OR pkw)')['query']).keywords
['bildschirm', 'fahrzeug', 'pkw']



From the wild
=============

Umlauts
-------

>>> DepaTechParser('AB:((*messschieber* OR *meßschieber*) AND *digital* )').dumps()
'((AB : *messschieber* or AB : *me\xdfschieber*) and AB : *digital*)'

>>> DepaTechParser('AB:((*messschieber* OR *meßschieber*) AND *digital* )').keywords
['messschieber', 'me\xdfschieber', 'digital']


More
----

>>> DepaTechParser('ET:(energy and water) or AB:(waves or Tide) and AB:"90°"').keywords
['energy', 'water', 'waves', 'Tide', '90\xb0']

>>> DepaTechParser('AB:(((bremsgefühl* or pedalgefühl) and (*simulator or simul*)) and (separ* or getrennt* or entkoppel* or entkoppl* or decoupl*) and (eigenständig* or independent* or autonom*))').keywords
['bremsgef\xfchl', 'pedalgef\xfchl', 'simulator', 'simul', 'separ', 'getrennt', 'entkoppel', 'entkoppl', 'decoupl', 'eigenst\xe4ndig', 'independent', 'autonom']
