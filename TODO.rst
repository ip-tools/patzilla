=========================
elmyra.ip.access.epo TODO
=========================

- Open Patent Services RESTful Web Services Reference Guide
  http://documents.epo.org/projects/babylon/eponot.nsf/0/2F88B7285FC1E3ECC125785500531278/$File/OPS_v3_1_documentation_version_1_2_7_en.pdf

Prio 1.1
========
- Big Layout changes
    - [/] Abstände und Einzüge homogener machen
        - z.B. Bei zwei Erfindern zum Abstract
    - [x] Datumsformatierung: erstmal ISO 2013-10-01, später locale-abhängig
    - [x] INID-Codes für Datumsangaben und IPC
    - [x] IPCs in den rechten Block, kommagetrennt; CPC auch; beides über den Abstract Block
    - [x] Icons
        - https://upload.wikimedia.org/wikipedia/commons/2/24/Adobe_PDF_Icon.svg
    - [x] Besserer "Add" Button
    - [x] Popovers für action buttons

    - [o] Alles englisch
    - [o] Karussel für die Bilder
    - [o] "Choose all"
    - [o] Tooltips für INID Einträge in bibl. Daten
    - [o] Idee: Embedding Feature mit iframe
        - http://demo08.europatentdienst.de/kunden/demo08/pmn.nsf/CommentExpert?OpenForm&PN=DE1234567A1
    - [o] jquery.shorten für Erfinder
    - [o] INID-Code variiert je nach Kind
    - [o] Patentnummer fetter, dicker Balken



Prio 1.2
========
- [x] Anzeige der Trefferanzahl
- [x] Anzeige first-drawing
    - load pictures
        - http://viralpatel.net/blogs/lazy-load-image-wordpress-avatar-jquery/
        - lazy-load and display first drawing below patent number
        - display inline images inside abstract text, e.g. WO2013153465A1, US2013270608A1,
- [x] PDF Anzeige
- [o] Link zur PDF Vollschrift
- [o] "Detailansicht": Fullscreen carousel für all-drawings mit Abstract und Claims
- [o] History/Warenkorb mit quadrupel (bookmark-date, number, title, stars)

Prio 1.3
========
- [o] parse "patent-classification" if "classification-ipcr" is not present!? (@ pn=US2013266007A1)
      => CPC Fallback
- [o] new usage ship-mode=single-bibdata
    - [x] data: display "inventor" attribute
    - [x] blueprint multiframe page having opsbrowser integrated with other tools on the same page
          https://tools.ip.elmyra.de/portfolio-demo?query=applicant=rational&ship-mode=single-bibdata&ship-url=https://httpbin.org/post&page-title=Portfolio%20Bewertung&page-subtitle=Schritt%201:%20Recherche%20bei%20OPS
    - [x] ui: use buttons instead of checkboxes
    - [x] query submit logic (by ship-mode; here: post all/common bibliographic data to ship-url)
    - [x] ui: hide basket
    - [o] introduce "ship-button-label", default="auswählen" (instead of hardcoded "bewerten")
- [o] "Help" screen
- [o] browser history / pushstate
      http://stackoverflow.com/questions/6638738/codeigniter-jqueryajax-html5-pushstate-how-can-i-make-a-clean-navigation/6639119#6639119
- [o] Lokalisierung english-only
- [o] Sharing: Patent with Picture (and Comment)
- [o] Aktive Merkliste => Klicken eines Detaildokuments führt zu Query-By-Document


Prio 1.5
========
- [o] beware of the CSRF/XSRF!!! (ship-url, page-title, page-subtitle, ship-button-label)
- [o] ui: display "version" from configfile
- [o] ui: use icons from iconset
    - icon index/overview pages
- [o] "select all" functionality
    - | Multiple Checkbox Select/Deselect
      |http://viralpatel.net/blogs/multiple-checkbox-select-deselect-jquery-tutorial-example/
- [o] show error messages from ops::

    2013-10-17 05:26:32,976 ERROR [waitress][Dummy-2] Exception when serving /api/ops/published-data/search
    Traceback (most recent call last):
      File "/opt/ops-chooser/.venv/lib/python2.6/site-packages/waitress/channel.py", line 332, in service
        task.service()
      [...]
        response = view_callable(exc, request)
      File "/opt/ops-chooser/.venv/lib/python2.6/site-packages/pyramid/config/views.py", line 397, in viewresult_to_response
        raise ValueError(msg % (view_description(view), result))
    ValueError: Could not convert return value of the view callable function cornice.pyramidhook.handle_exceptions into a response object. The value returned was AttributeError("'_JSONError' object has no attribute 'detail'",).

- [o] paging:
    - [x] simple/static pager ui
    - [o] basketstate-to-checkbox backpropagation
    - [o] dynamic pager
    - [o] show current response range
- [o] use buttons with "Select" label instead of checkboxes
    http://bootsnipp.com/snipps/select-users
- [o] Add text, fields and examples from "Open Patent Services RESTful Web Services Reference Guide » 4.2. CQL index catalogue"
  http://documents.epo.org/projects/babylon/eponot.nsf/0/2F88B7285FC1E3ECC125785500531278/$File/OPS_v3_1_documentation_version_1_2_7_en.pdf
- [o] react on "no records" and display it somehow
- [o] searching with spaces, e.g. "inventor=moritz hilger" or "applicant=RATIONAL INTELLECTUAL HOLDINGS LTD" throws 500 errors
- [o] display and use some metadata information from ops response envelope
- [o] Marken: curl --silent -XPOST --data 'start=0&rows=15&criterion_1=ApplicantName&term_1=Grohe+AG&operator_1=AND&condition_1=CONTAINS&sortField=ApplicationNumber&sortOrder=asc' https://oami.europa.eu/copla/ctmsearch/json | python -mjson.tool

Prio 2
======
- convert pub.-date format to german locale using fine javascript library X
- display other general data from ops response (record count, range, etc.)
- display country flags:
    - patent country
    - applicant countries from "epodoc" value
- enrich data
    - wordcount and wordle of abstract
- Direktlinks zum OPS (HTML, XML, JSON, PDF)
- test: swap Titel, Anmelder, ... column with content column
- [14.10.13 19:25:43] Janosch: weißt was noch schön wär:
    shift+enter -> nachste zeile
    enter -> datenbank abfragen
- make some detail attributes collapsible
- Navigation: replace hashtag in url
- minify and **uglify** via bower / production.ini
- make table responsive, e.g. by using twitter bootstrap 3 or FooTable ( http://fooplugins.com/plugins/footable-jquery/ )
- render reports using embedded webkit


Prio 3
======
- http://viralpatel.net/blogs/jquery-not-selector-example/
- UY34620A
- ship-* parameters

    ops-chooser integration query parameters:

    - ingress:
        - query

    - egress:
        - ship-mode:   default="multi-numberlist", other values: "single-bibdata"
        - ship-method: default="http-post", might be "ftp" as well ;])
        - ship-url
        - ship-param: default="payload"
        - ship-format default="text" (or related to ship-mode's default), might be "json" or "xml"
- display ship-* parameters with overlay
- infinite scrolling


Prio 4
======
- get more from the data, e.g.
    - query by applicant, show first and most recent publication dates
    - query by applicant, show patent publications as timeline
- semantically enrich "abstract" content
    - decode all references and acronyms
    - e.g.
        US2013275937A1, US2013275704A1, US2013275667A1, WO2013153472A1, WO2013153755A1,
        US2013270561A1, US2013265085A1, US2013264653A1, US2013264641A1, US2013268694A1,

Bugs
====
- [o] Trefferanzahl geht irgendwann weg

Done
====
- http://bootsnipp.com/snipps/twitter-like-message-box
- setup on https://tools.ip.elmyra.de/ops-chooser
- integration with lotus notes
    - http://www.tlcc.com/admin/tips.nsf/tipurlref/20041108
    - http://www-01.ibm.com/support/docview.wss?uid=swg21111823
- tune textarea widths
- introduce ship-* parameter convention
    - rename "came_from" to "ship-url"
    - get "ship-param=NumberList" form query param
- disable javascript resource caching
- fix "abstract" parsing, e.g. @ WO2013148409A1
- applicant=ibm => cannot use method "join" on undefined
- neu: anmeldedatum
- show spinner while loading, from fontawesome
- Uncaught TypeError: Cannot read property 'p' of undefined:  @ DE1521311A1 and HRP20130820T1
- title "?MÉTODO Y SISTEMA PARA INSTANCIAS DE FUNCIONAMIENTO DE UN JUEGO?." @ UY34621A => ist okay, da in den Original XML Daten auch genauso vorhanden
- title padding
- display (pull-right): ops-chooser v0.0.x in title
