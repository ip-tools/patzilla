.. -*- coding: utf-8 -*-
.. (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

===========================================
CQL pyparsing parser tests: Foundation spec
===========================================

This tests all examples from https://en.wikipedia.org/wiki/Contextual_Query_Language

>>> from patzilla.util.cql.pyparsing import CQL


Empty query
===========
>>> CQL('').dumps()
''


Simple queries
==============

>>> CQL('dinosaur').dumps()
'dinosaur'

>>> CQL('"complete dinosaur"').dumps()
'"complete dinosaur"'

>>> CQL('title = "complete dinosaur"').dumps()
'title="complete dinosaur"'

>>> CQL('title exact "the complete dinosaur"').dumps()
'title exact "the complete dinosaur"'


Queries using Boolean logic
===========================

>>> CQL('dinosaur or bird').dumps()
'dinosaur or bird'

.. note:: **FIXME: enhance grammar**

>>> #CQL('Palomar assignment and "ice age"').dumps()

>>> CQL('dinosaur not reptile').dumps()
'dinosaur not reptile'

>>> CQL('dinosaur and bird or dinobird').dumps()
'dinosaur and bird or dinobird'

>>> CQL('(bird or dinosaur) and (feathers or scales)').dumps()
'(bird or dinosaur) and (feathers or scales)'

>>> CQL('"feathered dinosaur" and (yixian or jehol)').dumps()
'"feathered dinosaur" and (yixian or jehol)'


Queries accessing publication indexes
=====================================

>>> CQL('publicationYear < 1980').dumps()
'publicationYear < 1980'

>>> CQL('lengthOfFemur > 2.4').dumps()
'lengthOfFemur > 2.4'

>>> CQL('bioMass >= 100').dumps()
'bioMass >= 100'


Queries based on the proximity of words to each other in a document
===================================================================

.. note:: **FIXME: enhance grammar**

>>> #CQL('ribs prox/distance<=5 chevrons').dumps()
>>> #CQL('ribs prox/unit=sentence chevrons').dumps()
>>> #CQL('ribs prox/distance>0/unit=paragraph chevrons').dumps()


Queries across multiple dimensions
==================================

>>> CQL('date within "2002 2005"').dumps()
'date within "2002 2005"'

>>> CQL('dateRange encloses 2003').dumps()
'dateRange encloses 2003'


Queries based on relevance
==========================

>>> CQL('subject any/relevant "fish frog"').dumps()
'subject any/relevant "fish frog"'

>>> CQL('subject any/rel.lr "fish frog"').dumps()
'subject any/rel.lr "fish frog"'
