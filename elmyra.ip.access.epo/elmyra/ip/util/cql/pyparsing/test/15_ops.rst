.. -*- coding: utf-8 -*-
.. (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

========================================
CQL pyparsing parser tests: OPS features
========================================

see also:

- http://documents.epo.org/projects/babylon/eponet.nsf/0/7AF8F1D2B36F3056C1257C04002E0AD6/$File/OPS_RWS_ReferenceGuide_version1210_EN.pdf

>>> from elmyra.ip.util.cql.pyparsing import CQL


Date range
==========

Test some date range conditions.

>>> CQL('publicationdate within 2014-03-10,2014-03-16').dumps()
u'publicationdate within 2014-03-10,2014-03-16'


Examples from OPS reference guide
=================================

see also:

- p. 152-153: http://documents.epo.org/projects/babylon/eponet.nsf/0/7AF8F1D2B36F3056C1257C04002E0AD6/$File/OPS_RWS_ReferenceGuide_version1210_EN.pdf


CQL examples
