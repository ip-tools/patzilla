=========================
elmyra.ip.access.epo TODO
=========================


Prio 0
======
- Uncaught TypeError: Cannot read property 'p' of undefined:  @ DE1521311A1 and HRP20130820T1
- parse "patent-classification" if "classification-ipcr" is not present!? (@ pn=US2013266007A1)
- title "?MÉTODO Y SISTEMA PARA INSTANCIAS DE FUNCIONAMIENTO DE UN JUEGO?." @ UY34621A


Prio 1
======
- new usage ship_kind=single-bibdata
    - blueprint multiframe page having opsbrowser integrated with other tools on the same page
    - ui: use buttons instead of checkboxes
    - query submit logic (by ship_kind; here: post all/common bibliographic data to ship_url)
    - ui: hide basket
    - ui: use icons from iconset
    - data: display "inventor" attribute


Prio 1.5
========
::

    2013-10-17 05:26:32,976 ERROR [waitress][Dummy-2] Exception when serving /api/ops/published-data/search
    Traceback (most recent call last):
      File "/opt/ops-chooser/.venv/lib/python2.6/site-packages/waitress/channel.py", line 332, in service
        task.service()
      [...]
        response = view_callable(exc, request)
      File "/opt/ops-chooser/.venv/lib/python2.6/site-packages/pyramid/config/views.py", line 397, in viewresult_to_response
        raise ValueError(msg % (view_description(view), result))
    ValueError: Could not convert return value of the view callable function cornice.pyramidhook.handle_exceptions into a response object. The value returned was AttributeError("'_JSONError' object has no attribute 'detail'",).

- paging:
    - [x] simple/static pager ui
    - [o] basketstate-to-checkbox backpropagation
    - [o] dynamic pager
    - [o] show current response range
- use buttons with "Select" label instead of checkboxes
    http://bootsnipp.com/snipps/select-users
- "select all" functionality
- Multiple Checkbox Select/Deselect
    - http://viralpatel.net/blogs/multiple-checkbox-select-deselect-jquery-tutorial-example/
- title padding
- display (pull-right): ops-chooser v0.0.x in title

- Add text, fields and examples from "Open Patent Services RESTful Web Services Reference Guide » 4.2. CQL index catalogue"
  http://documents.epo.org/projects/babylon/eponot.nsf/0/2F88B7285FC1E3ECC125785500531278/$File/OPS_v3_1_documentation_version_1_2_7_en.pdf
- react on "no records" and display it somehow
- show error messages from ops


Prio 2
======
- load pictures
    - http://viralpatel.net/blogs/lazy-load-image-wordpress-avatar-jquery/
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


Prio 3
======
- http://viralpatel.net/blogs/jquery-not-selector-example/
- UY34620A
- "Help" screen
- ship_* parameters

    ops-chooser integration query parameters:

    - ingress:
        - query

    - egress:
        - ship_method: default="http-post", might be "ftp" as well ;])
        - ship_url
        - ship_param: default="payload"
        - ship_kind:  default="multi-numberlist", might be "details", etc.
        - ship_format default="text" (or related to ship_kind's default), might be "json" or "xml"
- display ship_* parameters with overlay
- infinite scrolling


Prio 4
======
- get more from the data, e.g.
    - query by applicant, show first and most recent publication dates
    - query by applicant, show patent publications as timeline


Done
====
- http://bootsnipp.com/snipps/twitter-like-message-box
- setup on https://tools.ip.elmyra.de/ops-chooser
- integration with lotus notes
    - http://www.tlcc.com/admin/tips.nsf/tipurlref/20041108
    - http://www-01.ibm.com/support/docview.wss?uid=swg21111823
- tune textarea widths
- introduce ship_* parameter convention
    - rename "came_from" to "ship_url"
    - get "ship_param=NumberList" form query param
- disable javascript resource caching
- fix "abstract" parsing, e.g. @ WO2013148409A1
- applicant=ibm => cannot use method "join" on undefined
- neu: anmeldedatum
- show spinner while loading, from fontawesome
