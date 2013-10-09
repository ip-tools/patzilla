=========================
elmyra.ip.access.epo TODO
=========================

Prio 0
======
- setup on https://tools.ip.elmyra.de/ops-chooser
- integration with lotus notes
    - http://www.tlcc.com/admin/tips.nsf/tipurlref/20041108
    - http://www-01.ibm.com/support/docview.wss?uid=swg21111823
- select all functionality
- paging; with basket backpropagation
- infinite scrolling
- Uncaught TypeError: Cannot read property '@lang' of undefined
    =>
- textarea widths

Prio 1
======
- fix "abstract" parsing, e.g. @ WO2013148409A1
- Multiple Checkbox Select/Deselect
    - http://viralpatel.net/blogs/multiple-checkbox-select-deselect-jquery-tutorial-example/
- rename "came_from" to "ship_url"
- get "ship_param=NumberList" form query param
- disable javascript resource caching
- Add text, fields and examples from "Open Patent Services RESTful Web Services Reference Guide » 4.2. CQL index catalogue"
  http://documents.epo.org/projects/babylon/eponot.nsf/0/2F88B7285FC1E3ECC125785500531278/$File/OPS_v3_1_documentation_version_1_2_7_en.pdf
- test: swap Titel, Anmelder, ... column with content column
- react on "no records" and display it somehow
- show spinner while loading, from fontawesome
- load pictures
    - http://viralpatel.net/blogs/lazy-load-image-wordpress-avatar-jquery/
- paging!
- applicant=ibm => cannot use method "join" on undefined
- anmeldedatum

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


Done
====
- http://bootsnipp.com/snipps/twitter-like-message-box
