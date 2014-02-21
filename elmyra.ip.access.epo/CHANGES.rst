============================
elmyra.ip.access.epo CHANGES
============================

development
===========
- ui: click on document-number in header to navigate to this document
- ui: enhance pager, display active pagination entry, display current range
- ui: open drill-down links in external window

0.4.0
=====
- api: add a little cql smartness: wrap cql query string with
       quotes if query contains spaces and is still unquoted
- api: enhance image information, publish via endpoint
- ui: carousel for drawings
- ui: display pager on top of and at bottom of resultlist
- ui: don't show pagers when there are no results yet
- ui: link to family information (INPADOC, OPS)
- ui: display cited references below abstract

0.3.0
=====
- middleware: create full pdf documents from single pages via ops only
- ui: offer full pdf document from multiple sources
- ui/middleware: apply links to applicants, inventors, ipc classes and publication date

0.2.2
=====
- middleware: add DPMAregister smart access subsystem
- api: publish DPMAregister smart access subsystem, e.g.
  /jump/dpma/register?pn=DE19630877
- ui: display link to uspto pair

0.2.1
=====
- ui/api: evaluate and display upstream error responses
- middleware: adjust image level while converting from tiff to png
- ui: remove (54) entry prefix
- ui: refactor header
- middleware: also cache output of tiff-to-png conversion for drawings
- ui: style header buttons inline with others (gray, not turquoise)
- ui: gray background, refactor query area
- ui: link to legal status information from various patent offices
  (European Patent Register, INPADOC legal status, DPMAregister)


0.2.0
=====
- ui: show alternative text when no drawing image is available instead of broken image symbol
- ui: download full pdf document from espacenet instead of having single-page images only
- ui: resize first drawing image to 457px width to avoid resizing in browsers
- ui/feature: "review" selected documents
- api/ui: propagate "numberlist" query parameter value into basket
- api/middleware: document-number normalization on patent-search endpoint for "pn=" attributes
- middleware: resource caching
    - search: 5 minutes
    - static: 1 year

0.1.1
=====
- pdf.svg problems: fix MANIFEST, fix setup.py

0.1.0
=====
- api: introduce new image kind "FullDocumentDrawing" which will return
  an url to a high resolution image ("FullDocument") of the first drawing page
- ui: major overhaul, move on from table-based to container-based listview
- ui: more appealing add-/remove-basket operation
- ui: format dates in ISO format
- ui: uppercase countrycodes
- ui: popovers for action buttons
- ui: add pdf icon
- ui: show parties (applicants, inventors) "original" value only, hide "epodoc" value
- ui: add page footer and product name
- ui: add tooltips and popovers
- ui: use english

0.0.12
======
- api endpoint for retrieving fullimage documents as pdf
- ui: modal pdf viewer with paging

0.0.11
======
- api endpoint for retrieving family publications in xml

0.0.10
======
- add ops oauth client
- inline display first drawing

0.0.9
=====
- show result count in pagination area
- application structure refactoring and streamlining
- prepare inline display of first drawing

0.0.8
=====
- ship-mode=single-bibdata: rename "submit" form button name to "ship_action"

0.0.7
=====

feature:
- backpropagate current basket entries into checkbox state
- display "inventor" attribute
- add portfolio demo frameset
- add ship-mode=single-bibdata
- fix: be more graceful if applicants or inventors are missing from data
- renamed ingress query parameters "ship_*" to "ship-*"

tech:
- route refactoring
- ui refactoring: more responsive through "twitter bootstrap responsive css"

0.0.6
=====
- fix "abstract" parsing

0.0.5
=====
- fix packaging and deployment issues

0.0.4
=====
- upgrade to 'js.marionette==1.1.0a2'

0.0.3
=====
- moved js.marionette to github
- enhanced deployment code "make install" reg. versioning
- fix "abstract" parsing, e.g. @ WO2013148409A1
- applicant=ibm => cannot use method "join" on undefined
- neu: anmeldedatum
- simple static paging from 1-200, 25 each
- spinner icon for showing activity

0.0.2
=====
- changed production.ini port to 9999
- renamed js.underscore.string to js.underscore_string
- Makefile and fabfile.py for common sysop tasks
- renamed some ingress query parameters to "ship_*"
- cleaned up url parameter propagation

0.0.1
=====
- initial release
- pyramid web application with cornice webservice addon
- rest endpoint for querying EPO OPS REST service (ops-published-data-search)
- top-notch frontend ui foundation based on jquery, bootstrap, backbone marionette, fontawesome
- packaged some fanstatic javascript libraries:
    - js.marionette
    - js.underscore_string
    - js.jquery_shorten
    - js.purl
- textarea for cql query input
- shipping subsystem via basket textarea
- use "query" url parameter
- send "pragma: nocache" for static resources for now
