.. -*- coding: utf-8 -*-
.. (c) 2015-2018 Andreas Motl <andreas.motl@ip-tools.org>

===============================
SIP CQL expression parser tests
===============================

>>> from pymongo.uri_parser import parse_uri
>>> from mongoengine import connect as mongoengine_connect
>>> from patzilla.access.sip.expression import SipCqlClass, SipCqlFulltext
>>> from patzilla.util.xml.format import compact_print


Setup MongoDB connection
========================

Database contains concordance maps for resolving countries and classes.

>>> mongodb_uri = 'mongodb://localhost:27017/patzilla_development'
>>> mongodb_database = parse_uri(mongodb_uri)['database']
>>> mongoengine_connect(mongodb_database, host=mongodb_uri)
MongoClient('localhost', 27017)


Empty query
===========
>>> SipCqlClass('').dumpxml()
''
>>> SipCqlFulltext('').dumpxml()
''


IPC queries
===========
>>> print(SipCqlClass('H01F7/00').dumpxml(pretty=True))
<or>
    <ipc SmartSelect="false">
        <ipcid>161403</ipcid>
    </ipc>
    <cpc SmartSelect="false">
        <cpcid>161403</cpcid>
    </cpc>
</or>

>>> print(SipCqlClass('H01F7/00 or H01F7/02').dumpxml(pretty=True))
<or>
    <or>
        <ipc SmartSelect="false">
            <ipcid>161403</ipcid>
        </ipc>
        <cpc SmartSelect="false">
            <cpcid>161403</cpcid>
        </cpc>
    </or>
    <or>
        <ipc SmartSelect="false">
            <ipcid>161404</ipcid>
        </ipc>
        <cpc SmartSelect="false">
            <cpcid>161404</cpcid>
        </cpc>
    </or>
</or>

>>> print(SipCqlClass('H01F7/00 or (H01F7/02 and H02K7/1876)').dumpxml(pretty=True))
<or>
    <or>
        <ipc SmartSelect="false">
            <ipcid>161403</ipcid>
        </ipc>
        <cpc SmartSelect="false">
            <cpcid>161403</cpcid>
        </cpc>
    </or>
    <and>
        <or>
            <ipc SmartSelect="false">
                <ipcid>161404</ipcid>
            </ipc>
            <cpc SmartSelect="false">
                <cpcid>161404</cpcid>
            </cpc>
        </or>
        <cpc SmartSelect="false">
            <cpcid>357466</cpcid>
        </cpc>
    </and>
</or>

>>> print(SipCqlClass('H01F7/00 and (H01F7/02 or H02K7/1876)').dumpxml(pretty=True))
<and>
    <or>
        <ipc SmartSelect="false">
            <ipcid>161403</ipcid>
        </ipc>
        <cpc SmartSelect="false">
            <cpcid>161403</cpcid>
        </cpc>
    </or>
    <or>
        <or>
            <ipc SmartSelect="false">
                <ipcid>161404</ipcid>
            </ipc>
            <cpc SmartSelect="false">
                <cpcid>161404</cpcid>
            </cpc>
        </or>
        <cpc SmartSelect="false">
            <cpcid>357466</cpcid>
        </cpc>
    </or>
</and>

>>> print(SipCqlClass('H01F7/00 not (H01F7/02 or H02K7/1876)').dumpxml(pretty=True))
<and>
    <or>
        <ipc SmartSelect="false">
            <ipcid>161403</ipcid>
        </ipc>
        <cpc SmartSelect="false">
            <cpcid>161403</cpcid>
        </cpc>
    </or>
    <not>
        <or>
            <or>
                <ipc SmartSelect="false">
                    <ipcid>161404</ipcid>
                </ipc>
                <cpc SmartSelect="false">
                    <cpcid>161404</cpcid>
                </cpc>
            </or>
            <cpc SmartSelect="false">
                <cpcid>357466</cpcid>
            </cpc>
        </or>
    </not>
</and>

>>> print(SipCqlClass('H01F7/00 and not (H01F7/02 or H02K7/1876)').dumpxml(pretty=True))
<and>
    <or>
        <ipc SmartSelect="false">
            <ipcid>161403</ipcid>
        </ipc>
        <cpc SmartSelect="false">
            <cpcid>161403</cpcid>
        </cpc>
    </or>
    <not>
        <or>
            <or>
                <ipc SmartSelect="false">
                    <ipcid>161404</ipcid>
                </ipc>
                <cpc SmartSelect="false">
                    <cpcid>161404</cpcid>
                </cpc>
            </or>
            <cpc SmartSelect="false">
                <cpcid>357466</cpcid>
            </cpc>
        </or>
    </not>
</and>

>>> SipCqlClass('H01F7/00 not (H01F7/02 or H02K7/1876)').dumpxml(pretty=True) == SipCqlClass('H01F7/00 and not (H01F7/02 or H02K7/1876)').dumpxml(pretty=True)
True

>>> print(SipCqlClass('not H01F7/02').dumpxml(pretty=True))
<not>
    <or>
        <ipc SmartSelect="false">
            <ipcid>161404</ipcid>
        </ipc>
        <cpc SmartSelect="false">
            <cpcid>161404</cpcid>
        </cpc>
    </or>
</not>


Full text queries
=================

>>> print(SipCqlFulltext('ti=bildschirm').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">bildschirm</text>

>>> print(SipCqlFulltext('ti=bildschirm or ab=fahrzeug').dumpxml(pretty=True))
<or>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">bildschirm</text>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug</text>
</or>

>>> print(SipCqlFulltext('ti=bildschirm or ab=(fahrzeug or pkw)').dumpxml(pretty=True))
<or>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">bildschirm</text>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug or pkw</text>
</or>

>>> print(SipCqlFulltext('ti=bildschirm and (ab=fahrzeug or ab=pkw)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">bildschirm</text>
    <or>
        <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug</text>
        <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">pkw</text>
    </or>
</and>

>>> print(SipCqlFulltext('ti=bildschirm and ab=(fahrzeug or pkw not lkw)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">bildschirm</text>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug or pkw not lkw</text>
</and>

>>> print(SipCqlFulltext('ab=fahrzeug or ab=pkw').dumpxml(pretty=True))
<or>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug</text>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">pkw</text>
</or>

>>> print(SipCqlFulltext('(ab=fahrzeug or ab=pkw)').dumpxml(pretty=True))
<or>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug</text>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">pkw</text>
</or>

>>> print(SipCqlFulltext('(ab=fahrzeug and ab=pkw)').dumpxml(pretty=True))
<and>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug</text>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">pkw</text>
</and>

>>> print(SipCqlFulltext('ab=(fahrzeug and pkw)').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug and pkw</text>

>>> print(SipCqlFulltext('ab=(fahrzeug pkw)').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug and pkw</text>


>>> print(SipCqlFulltext('ab=fahrzeug not ti=pkw').dumpxml(pretty=True))
<and>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">fahrzeug</text>
    <not>
        <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">pkw</text>
    </not>
</and>


Expressions with proximity operators
====================================

Queries based on the proximity of words to each other in a document.

>>> print(SipCqlFulltext('ab=(pitch near,2 angle)').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">near(pitch angle, 2)</text>

>>> print(SipCqlFulltext('bi=(pitch near,2 angle)').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">near(pitch angle, 2)</text>


>>> print(SipCqlFulltext('bi=(convert and electric and mechanic)').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">convert and electric and mechanic</text>


>>> print(SipCqlFulltext('bi=(waves span,5 energy) and bi=(*convert* and *electric* and *mechanic*)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">span(waves energy, 5)</text>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">*convert* and *electric* and *mechanic*</text>
</and>




Expressions without qualifying fieldnames
=========================================

Queries without proper fieldnames like ab=, ti=, bi=, etc. on the left side of the term.

>>> print(SipCqlFulltext('bildschirm').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">bildschirm</text>

>>> print(SipCqlFulltext('bildschirm and fahrzeug').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">bildschirm and fahrzeug</text>

>>> print(SipCqlFulltext('not bildschirm').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">not bildschirm</text>

>>> print(SipCqlFulltext('not(bildschirm)').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">not bildschirm</text>

>>> print(SipCqlFulltext('not(bildschirm or fahrzeug)').dumpxml(pretty=True))
<not>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">bildschirm or fahrzeug</text>
</not>

>>> print(SipCqlFulltext('fahrzeug not pkw').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">fahrzeug not pkw</text>

>>> print(SipCqlFulltext('pitch near,2 angle').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">near(pitch angle, 2)</text>

>>> print(SipCqlFulltext('waves span,5 energy').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">span(waves energy, 5)</text>

>>> print(SipCqlFulltext('(waves span,5 energy) and ((*convert* or *conversion*) and *electric* and *mechanic*)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">span(waves energy, 5)</text>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">(*convert* or *conversion*) and *electric* and *mechanic*</text>
</and>


Expressions containing quoted words
===================================

>>> print(SipCqlFulltext('"bildschirm"').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">"bildschirm"</text>

>>> print(SipCqlFulltext('ab="bildschirm"').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">"bildschirm"</text>

>>> print(SipCqlFulltext('bi=(waves span,5 energy) and bi=("convert" and "electric" and "mechanic")').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">span(waves energy, 5)</text>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">"convert" and "electric" and "mechanic"</text>
</and>

>>> print(SipCqlFulltext('bi=(waves span,5 energy) and bi=(("convert" or "conversion") and "electric" and "mechanic")').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">span(waves energy, 5)</text>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">("convert" or "conversion") and "electric" and "mechanic"</text>
</and>



Keyword extraction
==================

>>> SipCqlClass('H01F7/00').keywords()
[u'H01F7/00']

>>> SipCqlClass('H01F7/00 not (H01F7/02 or H02K7/1876)').keywords()
[u'H01F7/00', u'H01F7/02', u'H02K7/1876']

>>> SipCqlFulltext('bildschirm').keywords()
[u'bildschirm']

>>> SipCqlFulltext('"bildschirm"').keywords()
[u'bildschirm']

>>> SipCqlFulltext('ti=bildschirm or ab=(fahrzeug or pkw)').keywords()
[u'bildschirm', u'fahrzeug', u'pkw']

>>> SipCqlFulltext('bi=(waves span,5 energy) and bi=("convert" and "electric" and "mechanic")').keywords()
[u'convert', u'electric', u'mechanic', u'waves', u'energy']

>>> SipCqlFulltext('bi=(waves span,5 energy) and bi=(("convert" or *conversion*) and "electric" and "mechanic")').keywords()
[u'convert', u'conversion', u'electric', u'mechanic', u'waves', u'energy']



Fantasy expressions
===================

Giving no fieldname qualifier, enable searching in all fulltext fields

>>> print(SipCqlFulltext('42').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">42</text>


Restricting search to "abstract" field should yield corresponding XML expression

>>> print(SipCqlFulltext('ab=42').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">42</text>


Quotes should be passed through

>>> print(SipCqlFulltext('ab="42"').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">"42"</text>


Corner case "parenthesis around the value"

>>> print(SipCqlFulltext('ab=(42)').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">42</text>


Corner case "parenthesis around the quoted value"

>>> print(SipCqlFulltext('ab=("42")').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">"42"</text>


Make sure things in quotes don't get parsed, things in quotes should be reproduced verbatim

>>> print(SipCqlFulltext('ab="42 and 23"').dumpxml(pretty=True))
<text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">"42 and 23"</text>

Also, without fieldname qualifier

>>> print(SipCqlFulltext('"42 and 23"').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">"42 and 23"</text>



From the wild
=============

Case sensitivity
----------------

>>> print(SipCqlFulltext('TI=(energy and water) and ab=(waves or Tide)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">energy and water</text>
    <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">waves or Tide</text>
</and>


Umlauts
-------

>>> print(SipCqlFulltext(u'ti=bremsgefühl').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">bremsgef&#252;hl</text>


Specials I
----------

>>> print(SipCqlFulltext(u'ti=(energy and water) or ab=(waves or Tide) and cl=90°').dumpxml(pretty=True))
<or>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">energy and water</text>
    <and>
        <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">waves or Tide</text>
        <text searchintitle="false" searchinabstract="false" searchinclaim="true" searchindescription="false" fullfamily="false">90&#176;</text>
    </and>
</or>

>>> print(SipCqlFulltext(u'ti=(energy and water) or (ab=(waves or Tide) and cl=90°)').dumpxml(pretty=True))
<or>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">energy and water</text>
    <and>
        <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">waves or Tide</text>
        <text searchintitle="false" searchinabstract="false" searchinclaim="true" searchindescription="false" fullfamily="false">90&#176;</text>
    </and>
</or>

>>> print(SipCqlFulltext(u'ti=(energy and water) or ((ab=waves or ab=Tide) and cl=90°)').dumpxml(pretty=True))
<or>
    <text searchintitle="true" searchinabstract="false" searchinclaim="false" searchindescription="false" fullfamily="false">energy and water</text>
    <and>
        <text searchintitle="false" searchinabstract="false" searchinclaim="true" searchindescription="false" fullfamily="false">90&#176;</text>
        <or>
            <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">waves</text>
            <text searchintitle="false" searchinabstract="true" searchinclaim="false" searchindescription="false" fullfamily="false">Tide</text>
        </or>
    </and>
</or>

>>> print(SipCqlFulltext(u'((bremsgefühl* or pedalgefühl) and (*simulator or simul*)) and (separ* or getrennt* or entkoppel* or entkoppl* or decoupl*) and (eigenständig* or independent* or autonom*)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">(bremsgef&#252;hl* or pedalgef&#252;hl) and (*simulator or simul*)</text>
    <and>
        <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">separ* or getrennt* or entkoppel* or entkoppl* or decoupl*</text>
        <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">eigenst&#228;ndig* or independent* or autonom*</text>
    </and>
</and>


Specials II
-----------

>>> print(SipCqlFulltext(u'(lochen* or perfor* or punch* or löcher* or pierc*) and (schlauch* or schläuche* or hose*)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">lochen* or perfor* or punch* or l&#246;cher* or pierc*</text>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">schlauch* or schl&#228;uche* or hose*</text>
</and>

>>> print(SipCqlFulltext(u'polymer and (lochen* or perfor* or punch* or löcher* or pierc*) and (schlauch* or schläuche* or hose*)').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">polymer</text>
    <and>
        <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">lochen* or perfor* or punch* or l&#246;cher* or pierc*</text>
        <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">schlauch* or schl&#228;uche* or hose*</text>
    </and>
</and>

>>> print(SipCqlFulltext(u'(lochen* or perfor* or punch* or löcher* or pierc*) and (schlauch* or schläuche* or hose*) and polymer').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">lochen* or perfor* or punch* or l&#246;cher* or pierc*</text>
    <and>
        <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">schlauch* or schl&#228;uche* or hose*</text>
        <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">polymer</text>
    </and>
</and>


Specials III
------------
>>> print(SipCqlFulltext(u'((small near,1 overlap) or *überdeck* or *überlapp* or (teil near,1 bedeck*) or teilbedeck*) and (ladeluftkühl* or *intercooler* or (air near,1 cooler))').dumpxml(pretty=True))
<and>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">(near(small overlap, 1)) or *&#252;berdeck* or *&#252;berlapp* or (near(teil bedeck*, 1)) or teilbedeck*</text>
    <text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">ladeluftk&#252;hl* or *intercooler* or (near(air cooler, 1))</text>
</and>


Specials IV
-----------
>>> print(SipCqlFulltext(u'(*einlage* or einlege*) near,2 (kunststoff* or pvc or cfk or gfk or fvk or aluminium* or magnesium*)').dumpxml(pretty=True))
<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="false">near((*einlage* or einlege*) (kunststoff* or pvc or cfk or gfk or fvk or aluminium* or magnesium*), 2)</text>

>>> SipCqlFulltext(u'(*einlage* or einlege*) near,2 (kunststoff* or pvc or cfk or gfk or fvk or aluminium* or magnesium*)').keywords()
[u'einlage', u'einlege', u'kunststoff', u'pvc', u'cfk', u'gfk', u'fvk', u'aluminium', u'magnesium']


Failures
========

>>> SipCqlFulltext('fahrzeug)')
Traceback (most recent call last):
    ...
ParseException: Expected end of text (at char 8), (line:1, col:9)


>>> SipCqlFulltext('"42')
Traceback (most recent call last):
    ...
ParseException: Expected """ (at char 3), (line:1, col:4)


>>> SipCqlFulltext('foo=bar')
Traceback (most recent call last):
    ...
FulltextDecodingError: SIP expression "foo=bar" contains unknown index "foo".
