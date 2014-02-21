=========================
elmyra.ip.access.epo TODO
=========================

Prio 1
======
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
    - [x] Alles englisch
    - [x] Tooltips für INID Einträge in bibl. Daten


Prio 2
======
- [x] PDF Anzeige in Firefox und Internet Explorer fixen => Volles PDF erzeugen [Lino, Michael, Jan]
- [x] Wenn keine Zeichnung geladen werden kann, besser alternativen Text statt zerbrochenem Bild anzeigen [Jan]
- [x] Bilder ordentlich auf gewünschte Breite skalieren (mit Antialiasing), IE rendert es sonst hässlich [Lino]
- [x] DE202013003344U1  (PDF kann nicht geöffnet werden in Chrome) [Michael]
- [x] Basket: "Review" button neben "Submit" button, soll nur die ausgewählten Schriften zur Anzeige bringen [Lino]
- [x] Nummern Normalisierung z.B. DE000019630877C2 vs. DE19630877C2 nach Kundenwunsch [Höfer via Jan]
- [x] Generic Caching Layer [Andi]
- [x] Evaluate and display search fault responses (message / details) [Andi]

- [x] (54) wieder weg [Lino]
- [x] header stil links/rechts gleich [Lino]
- [x] buttons grau [Lino]
- [x] hintergrund grau [Lino]
- [x] link zum register (with paragraph symbol) [Lino]

- [x] internal server error @ /api/ops/GB2505130.A/image/drawing
- [x] dpmaregister mit autobrowser + generische redirect schnittstelle
- [x] uspto pair access; entweder direktlink, oder zur einstiegsseite
- [/] business rules für register-links [Andi]

- [x] PDF selbst erzeugen(!!!) [Andi, Lino]
- [x] PDF erzeugen: internal server error bei /api/ops/DE69534171T2/pdf/all
- [x] PDF erzeugen: internal server error bei /api/ops/US5572526A/pdf/all
- [x] "BROWSE" feature: drill down into data (link applicant, inventor, ipc class, ...)


Prio 3
======
- [x] Karussell für die Bilder [Andi, Lino]
- [x] Paging Area auch unten anbringen! [Michi]
- [x] Familienrechtsstand @ Inpadoc EPO [Lino]
    - http://ops.epo.org/3.0/rest-services/family/publication/docdb/EP.2070806.B1/biblio,legal
- [x] Es wäre cool, wenn unter dem Abstract auch die Zitierten Schriften angezeigt
      werden würden, jeweils mit einem Link auf die Vollschrift. [Lino]


Prio 4
======
- [x] click on patent number to reach single view [Andi]
- [x] show current result range [Andi]
- [x] don't show "Drawing: 1" if there's no image [Andi]
- [x] drawing carousel: Show total number of drawings in gui [Andi]

- [o] [BUG] Gibts Bilder für z.B. AT9273U1, wenn man nach AT009273U1 schaut? [Andi]
- [o] [BUG] /api/ops/CH697931B1/image/drawing 500 (Internal Server Error) [Andi]
- [o] [BUG] /api/ops/CH697216B1/image/drawing 500 (Internal Server Error) [Andi]
- [o] [ANOMALY] "72) inventors RETO RUEEGGER" is shown, but search for "RUEEGGER RETO" would be better ;-) [Andi]
- [o] [BUG] UI-BEHAVIOUR: Dokumenteintrag "schnappt zusammen", wenn Bild nachgeladen wird => "min-height" setzen!?
- [o] [FEATURE] click on drawing should open high resolution version, maybe with zoom lens function

Prio 5.0
========
- [x] [UX] links extern öffnen [Lino]
- [x] [UX] pfeile karussel nach unten [Lino]
- [x] [UX] Drawing: mittig [Lino]
- [o] [FEATURE] legal infos ranholen und inline anzeigen [Andi]
- [o] [LEGAL] "BETA" badge [Andi]
- [o] [LEGAL] Disclaimer [Andi]
- [o] [BUG] CH706742B1 führt zu falscher DPMAregister seite [Andi, Lino]
- [o] [REFACTOR] /jump => /api/jump [Andi]
- [o] [IDEA] spawn mit referenz => html titel [Lino]
- [o] [IDEA] datepicker [Lino]

Prio 5.5
========
- [o] Embedding Feature mit iframe [Lino]
    - z.B. http://demo08.europatentdienst.de/kunden/demo08/pmn.nsf/CommentExpert?OpenForm&PN=DE1234567A1
- [o] Query builder + query help (feldnamen)
    https://depatisnet.dpma.de/DepatisNet/depatisnet?action=experte

- [o] Ansprechende und ausführliche Dokumentation für alle Parameter [Andi]
- [o] Bug: CH706742B1ww

      File "/Users/amo/dev/elmyra/elmyra.ip.access.epo/elmyra.ip.access.epo/elmyra/ip/access/epo/ops.py", line 69, in inquire_images
        patent = p['country'] + p['number'] + '.' + p['kind']
- [o] thumbnail view: http://getbootstrap.com/2.3.2/components.html#thumbnails
- [o] DPMAregister: nicht anhängig/erloschen Status inline lazy anzeigen
- [o] hide (56) (citations) if content is empty (maybe apply to all INID fields)

- [o] refactoring
    - LinkMaker


Prio 6
======
- [o] browser history / pushstate
      http://stackoverflow.com/questions/6638738/codeigniter-jqueryajax-html5-pushstate-how-can-i-make-a-clean-navigation/6639119#6639119
- [o] Mail shipping feature
- [o] Annotations feature
- [o] Local history feature (breadcrumb, tagcloud)
- [o] Link to online bibliographic database
- [o] Meta: Feature tracker / Ticket system => Trac

- [o] deliver svg placeholder, if tiff/png fails::

      <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
          <text x="200" y="40">No drawing available.</text>
      </svg>

- [o] POS tagging of interesting keywords
- [o] intercept paste handler to reformat numberlist
    - https://stackoverflow.com/questions/13964592/jquery-intercepting-paste-event/13964699#13964699
    - intelligent detection and handling of
        - patent number (and lists)
        - inventor name (and lists)
- [o] gerastertes scrolling von eintrag zu eintrag


Prio 7
======
- [o] Image rotation, e.g. EP2697738A1
- [o] "Choose all"
- [o] jquery.shorten für Erfinder [Lino]
- [o] INID-Code variiert je nach "patent *kind*" [Lino]
- [/] Patentnummer fetter, dicker Balken, falls selektiert [Andi, Lino]
- [o] Checkbox auf der linken Seite wiedereinführen, aber schöner, grafischer [Jan]
- [o] use app-pagename et al. in html title as well!


Prio 8
======

- [o] interlink documents (bibliographic data) and searches with other offices
    - DEPATISnet
        - https://depatisnet.dpma.de/
    - EPO Publications
        - https://data.epo.org/publication-server/?lg=en
    - Espacenet
        - http://worldwide.espacenet.com/publicationDetails/inpadocPatentFamily?CC=CH&NR=706742B1&KC=B1&FT=D&ND=&date=20140131&DB=&&locale=en_EP
    - Patentscope
        - http://patentscope.wipo.int/search/en/detail.jsf?docId=EP12638285
        - http://www.wipo.int/patentscope/search/en/result.jsf?query=ALLNUM:US20060123456
    - Google:
        - https://www.google.com/patents/WO2012055913A2
        - https://www.google.com/search?tbm=pts&q=inassignee:%22Mammut+Sports+Group+Ag%22
        - https://www.google.com/search?tbm=pts&q=ininventor:%22moritz+hilger%22
    - CCD Viewer
        - http://ops.epo.org/3.0/rest-services/published-data/search/biblio/.json?q=PN%3DEP%20AND%20(NUM%3DEP1612402%20OR%20NUM%3D1612402)&range=1-25
        - http://ops.epo.org/3.0/rest-services/published-data/publication/epodoc/JP2010043647/fulltext.json
        - http://ccd.fiveipoffices.org/CCD-2.0/html/viewCcd.html?num=CH20130000292&type=application&format=epodoc
        - http://ccd.fiveipoffices.org/CCD-2.0/html/viewCcd.html?num=EP20040425480&type=application&format=epodoc
        - http://ccd.fiveipoffices.org/CCD-2.0/html/viewCcd.html?num=JP2009214944&type=application&format=epodoc
    - FreePatentsOnline
    - http://www.intellogist.com/wiki/Compare:Patent_Search_System

- [o] feature: sort/group by country


Prio 9
======
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

Prio 10
=======
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
- [o] Lokalisierung english-only
- [o] Sharing: Patent with Picture (and Comment)
- [o] Aktive Merkliste => Klicken eines Detaildokuments führt zu Query-By-Document


Prio 11
=======
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

Prio 12
=======
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


Prio 13
=======
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


Prio 14
=======
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
