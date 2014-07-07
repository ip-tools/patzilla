.. -*- coding: utf-8 -*-
.. (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

========================================
CQL pyparsing parser tests: OPS features
========================================

see also:

- `Open Patent Services RESTful Web Services Reference Guide`_

.. _Open Patent Services RESTful Web Services Reference Guide: http://documents.epo.org/projects/babylon/eponet.nsf/0/7AF8F1D2B36F3056C1257C04002E0AD6/$File/OPS_RWS_ReferenceGuide_version1210_EN.pdf

>>> from elmyra.ip.util.cql.pyparsing import CQL


Date range
==========

Test date range condition used when extrapolating from vanity url, e.g. /publicationdate/2014W10.

>>> CQL('publicationdate within 2014-03-10,2014-03-16').dumps()
u'publicationdate within 2014-03-10,2014-03-16'


Examples from OPS reference guide
=================================

see also:

- `Open Patent Services RESTful Web Services Reference Guide`_, p. 152-153


CQL examples
------------

>>> CQL('ti all "green, energy"').dumps()
u'ti all "green, energy"'

.. note:: **FIXME: enhance grammar**

>>> #CQL('ti=green prox/unit=world ti=energy').dumps()

>>> CQL('pd within "20051212 20051214"').dumps()
u'pd within "20051212 20051214"'

>>> CQL('pd="20051212 20051214"').dumps()
u'pd="20051212 20051214"'

>>> CQL('ia any "John, Smith"').dumps()
u'ia any "John, Smith"'

>>> CQL('pn=EP and pr=GB').dumps()
u'pn=EP and pr=GB'

.. note:: **FIXME: enhance grammar**

>>> #CQL('ta=green prox/distance<=3 ta=energy').dumps()
>>> #CQL('ta=green prox/distance<=2/ordered=true ta=energy').dumps()
>>> #CQL('(ta=green prox/distance<=3 ta=energy) or (ta=renewable prox/distance<=3 ta=energy)').dumps()

>>> CQL('pa all "central, intelligence, agency" and US').dumps()
u'pa all "central, intelligence, agency" and US'

>>> CQL('pa all "central, intelligence, agency" and US and pd>2000').dumps()
u'pa all "central, intelligence, agency" and US and pd > 2000'

>>> CQL('pd < 18000101').dumps()
u'pd < 18000101'

>>> CQL('ta=synchroni#ed').dumps()
u'ta=synchroni#ed'

>>> CQL('EP and 2009 and Smith').dumps()
u'EP and 2009 and Smith'


.. note:: **FIXME: enhance grammar**

| p. 149: "a relational qualifier (=/low, =/high, =/same) can be used with CPC classification indices only"

>>> #CQL('cpc=/low A01B').dumps()


Shortcut notation expansion
---------------------------

All these should not be affected by any query manipulation. Prove that.

>>> CQL('pa all "central, intelligence, agency" and US').polish().dumps()
u'pa all "central, intelligence, agency" and US'

>>> CQL('pa all "central, intelligence, agency" and US and pd>2000').polish().dumps()
u'pa all "central, intelligence, agency" and US and pd > 2000'

>>> CQL('EP and 2009 and Smith').polish().dumps()
u'EP and 2009 and Smith'
