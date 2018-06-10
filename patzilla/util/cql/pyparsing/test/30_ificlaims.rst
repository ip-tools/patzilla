.. -*- coding: utf-8 -*-
.. (c) 2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

===============================================
CQL pyparsing parser tests: IFI CLAIMS features
===============================================

see also:

- https://confluence.ificlaims.com:8090/display/PUB20beta/CLAIMS+Direct+Documentation
- https://confluence.ificlaims.com:8090/display/PUB20beta/Search
- https://confluence.ificlaims.com:8090/display/PUB20beta/2016/02/29/Understanding+the+SOLR+Result+Set+-+sort+parameter


>>> from patzilla.access.dpma.depatisnet import DpmaDepatisnetAccess
>>> from patzilla.access.ificlaims.expression import IFIClaimsGrammar, IFIClaimsExpression
>>> def CQL(expression):
...     from patzilla.util.cql.pyparsing import CQL as UpstreamCQL
...     return UpstreamCQL(expression, grammar=IFIClaimsGrammar, keyword_fields=IFIClaimsExpression.fieldnames)




Logic operators localized
=========================

Test some logic operators localized to german.

Getting started
---------------
>>> CQL('pnctry:EP AND text:vibrat*').dumps()
u'pnctry : EP and text : vibrat*'

Made up
-------
Try to understand the query.

>>> CQL(u'(pnctry:EP and (pnctry:EP AND text:vibrat* AND (ic:G01F000184 OR cpc:G01F000184)))').dumps()
u'(pnctry : EP and (pnctry : EP and text : vibrat* and (ic : G01F000184 or cpc : G01F000184)))'

Extract keywords from query.

>>> CQL(u'(pnctry:EP and (pnctry:EP AND text:vibrat* AND (ic:G01F000184 OR cpc:G01F000184)))').polish().keywords()
[u'vibrat', u'G01F000184', u'G01F000184']
