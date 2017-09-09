.. -*- coding: utf-8 -*-
.. (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

==============================================
CQL pyparsing parser tests: Generic extensions
==============================================

>>> from patzilla.access.epo.ops.api import ops_keyword_fields
>>> from patzilla.access.dpma.depatisnet import DpmaDepatisnetAccess
>>> def CQL(expression):
...     from patzilla.util.cql.pyparsing import CQL as UpstreamCQL
...     return UpstreamCQL(expression, keyword_fields=ops_keyword_fields + DpmaDepatisnetAccess.keyword_fields)


Patent number normalization
===========================

First, check parsing and reproducing a query for a publication number without normalization applied:

>>> CQL('pn=EP666666').dumps()
u'pn=EP666666'


Then, check whether normalization works correctly. Here, the EP document number should get zero-padded properly:

>>> CQL('pn=EP666666').normalize_numbers().dumps()
u'pn=EP0666666'


Keyword extraction
==================

First, make sure the query can actually be parsed:

>>> CQL('bi=greifer and pc=de').dumps()
u'bi=greifer and pc=de'


Then, check the list of extracted keywords:

>>> CQL('bi=greifer and pc=de').keywords()
[u'greifer']


Details
-------

The keyword extractor has a whitelist of index names of all
relevant (text-)fields to only extract keywords from them.
That's the reason for "de" not appearing in the list of keywords above,
because index name "pc" is not whitelisted.

We can have a look at the layer below, where raw triples got extracted from the query string,
that's the step just before collecting the keywords:

>>> CQL(u'bi=greifer and pc=de').triples()
[[u'bi', u'=', u'greifer'], [u'pc', u'=', u'de']]

This shows we also have access to the "pc=de" condition if
there's demand for enhanced query analytics in the future.


Value shortcut notation
=======================

Nested expression
-----------------

Parse and reproduce a cql query containing a nested expression in value shortcut notation.
Our old token-based parser wasn't capable doing this.

>>> CQL('bi=(socke and (Inlay or Teile)) and pc=de').dumps()
u'bi=(socke and (Inlay or Teile)) and pc=de'


Expand the value shortcut notation:

>>> CQL('bi=(socke and (Inlay or Teile)) and pc=de').expand_shortcuts().dumps()
u'(bi=socke and (bi=Inlay or bi=Teile)) and pc=de'


Special operators
=================

Boolean operators (binops) in german
------------------------------------

>>> CQL('BI=Socke und PA=onion').dumps()
u'BI=Socke UND PA=onion'




All together now!
=================

In this section, multiple features are used at once by making up a query containing:

- a value shortcut notation for patent numbers which should be normalized after shortcut expansion,
- a CPC class containing a forward slash and
- a fulltext search condition with wildcard.

>>> query = 'pn=(EP666666 or EP666667) or (cpc=H04L12/433 and txt=communication?)'


Verbatim reproduction
---------------------
The query should be reproduced verbatim when not applying any expansion or normalization:

>>> CQL(query).dumps()
u'pn=(EP666666 or EP666667) or (cpc=H04L12/433 and txt=communication?)'


Polishing
---------
After shortcut expansion and number normalization, we should see zero-padded EP document numbers:

>>> CQL(query).polish().dumps()
u'(pn=EP0666666 or pn=EP0666667) or (cpc=H04L12/433 and txt=communication?)'

Terms from conditions for classification- or fulltext-indexes should count towards keywords:

>>> CQL(query).polish().keywords()
[u'H04L12/433', u'communication']


Details
-------
Even without polishing the query, the keywords should be the same,
since "cpc" and "txt" conditions both are not in value shortcut notation.

>>> CQL(query).keywords()
[u'H04L12/433', u'communication']

On the other hand, number normalization for numbers in value shortcut notation
obviously does not work when not having shortcut expansion applied before:

>>> CQL('pn=(EP666666 or EP666667)').normalize_numbers().dumps()
u'pn=(EP666666 or EP666667)'


Nesting and keywords
--------------------

We especially want to properly extract keywords from nested expressions,
even when they are in value shortcut notation.

>>> CQL('bi=(socke and (Inlay or Teile)) and pc=de').expand_shortcuts().keywords()
[u'socke', u'Inlay', u'Teile']
