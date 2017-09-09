.. -*- coding: utf-8 -*-
.. (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

====================================================
CQL pyparsing parser tests: Miscellaneous and errors
====================================================

This tests miscellaneous query features and erroneous queries.

>>> from patzilla.util.cql.pyparsing import CQL


Queries with UTF-8 characters
=============================

Try parsing a query containing utf-8 characters.

>>> CQL(u'title=molécules').dumps()
u'title=mol\xe9cules'

>>> CQL(u'inventor="CEGARRA SERRANO JOSÉ MARIANO"').dumps()
u'inventor="CEGARRA SERRANO JOS\xc9 MARIANO"'

>>> CQL(u'ab=radaufstandskraft or ab=radaufstandskräfte?').dumps()
u'ab=radaufstandskraft or ab=radaufstandskr\xe4fte?'

# TODO: use more esoteric utf-8 characters, e.g. special chars et al.

Queries using wildcards
=======================

>>> CQL('txt=footw or txt=footw? or txt=footw# or txt=footw! and txt=footw*re').dumps()
u'txt=footw or txt=footw? or txt=footw# or txt=footw! and txt=footw*re'


Query with comments
===================
>>> CQL("""
...
...    foo=(bar and        -- comment 1
...        (baz or qux))   -- comment 2
...
...    """).dumps()
u'foo=(bar and (baz or qux))'


Weird queries
=============
>>> CQL('   foobar   ').dumps()
u'foobar'

>>> CQL('(((foobar)))').dumps()
u'(((foobar)))'


Queries with errors
===================

Nonsense
--------
>>> CQL('foo bar', logging=False).dumps()
Traceback (most recent call last):
    ...
ParseException: Expected end of text (at char 4), (line:1, col:5)

Lacking terms
-------------
>>> CQL('foo=', logging=False).dumps()
Traceback (most recent call last):
    ...
ParseException: Expected term (at char 4), (line:1, col:5)

>>> CQL('foo= and bar=', logging=False).dumps()
Traceback (most recent call last):
    ...
ParseException: Expected end of text (at char 9), (line:1, col:10)

Unbalanced parentheses
----------------------
>>> CQL('(foo=bar', logging=False).dumps()
Traceback (most recent call last):
    ...
ParseException: Expected ")" (at char 8), (line:1, col:9)

>>> CQL('foo=bar)', logging=False).dumps()
Traceback (most recent call last):
    ...
ParseException: Expected end of text (at char 7), (line:1, col:8)

Unknown binops
--------------
>>> CQL('foo % bar', logging=False).dumps()
Traceback (most recent call last):
    ...
ParseException: Expected end of text (at char 4), (line:1, col:5)

Error explanation
-----------------
>>> try:
...     CQL(u'foo bar', logging=False).dumps()
... except Exception as ex:
...     ex.explanation
u'foo bar\n    ^\n\nExpected end of text (at char 4), (line:1, col:5)'
