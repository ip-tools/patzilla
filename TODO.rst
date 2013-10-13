=========================
elmyra.ip.access.epo TODO
=========================

Prio 0
======
- fix "abstract" parsing, e.g. @ WO2013148409A1
- applicant=ibm => cannot use method "join" on undefined
- anmeldedatum

Prio 1
======
- "select all" functionality
- Multiple Checkbox Select/Deselect
    - http://viralpatel.net/blogs/multiple-checkbox-select-deselect-jquery-tutorial-example/
- paging; with basketstate-to-checkbox backpropagation
- paging!
- spinner when network action is taking place
- Uncaught TypeError: Cannot read property '@lang' of undefined
    =>
- title padding
- display (pull-right): ops-chooser v0.0.x in title

- Add text, fields and examples from "Open Patent Services RESTful Web Services Reference Guide » 4.2. CQL index catalogue"
  http://documents.epo.org/projects/babylon/eponot.nsf/0/2F88B7285FC1E3ECC125785500531278/$File/OPS_v3_1_documentation_version_1_2_7_en.pdf
- react on "no records" and display it somehow
- show spinner while loading, from fontawesome

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
        - ship_kind:  default="numberlist", might be "details", etc.
        - ship_format default="text" (or related to ship_kind's default), might be "json" or "xml"
- display ship_* parameters with overlay
- infinite scrolling


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
