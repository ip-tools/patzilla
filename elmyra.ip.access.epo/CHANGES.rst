============================
elmyra.ip.access.epo CHANGES
============================

development
===========
- ui, middleware: propagate ops-specific fulltext fields to keyword highlighter
- ui: link to DEPATISnet PDF
- ui: prefer canonical epodoc values over original ones for parties (applicant, inventor) to increase search quality
- ui: enhance keyword highlighting: per-phrase vs. per-word
- ui: review action: just use single button above the query area
- ui: move basket submit button to the right side
- ui: show "current view count" and "real ops querystring" only in debug mode (by appending "&debug=true" to the url)
- ui: attempt to fix IE SVG problem: img declaration may have lacked "height" attribute
- ui: move "About CQL" away from main gui into help modal dialog (help prototype)
- ui: use magnifier icon for query submit button
- ui: stick query action buttons (transform, clear) to the right of the CQL field chooser
- ui: remove "Your selection" label, replace by placeholder on basket textarea
- ui: add placeholder to CQL field chooser

0.8.1
=====
- link javascript resources

0.8.0
=====
- ui: bind search to meta+return and ctrl+return keys
- ui: use explicit clipboard/query transformation (remove on.paste handler, add button)
- ui: use fixed name "ipsuite-pdf" for displaying the pdf
- ui: pagination: refactor into component
- ui: pagination: show only required paging entries, show nothing without results
- ui, middleware: enhance DEPATISnet integration
    - parse hit count from scraped response
    - fix page offset calculation
    - show original- and ops-queries
    - fix pagination problems in general
    - show count of items received from ops
    - scrape results with sort order: publication date, descending
- ui: properly propagate "datasource" query parameter, using sensible defaults, giving DEPATISnet priority
- ui: dpma- and epo-logos for datasource selector buttons
- ui: basket review: use the same mechanics as with DEPATISnet, i.e. splice list into bundles of 10 entries
- middleware: cache search queries for two hours
- ui: format total result count using jquery-autonumeric
- ui: add some hotkeys:
    - ctrl+shift+o: switch to datasource=ops
    - ctrl+shift+d: switch to datasource=depatisnet
    - ctrl+shift+r: switch to review mode

0.7.4
=====
- update jquery.hotkeys.js
- ui: remove "beta" badge
- ui: bind search to hyper+return and ctrl+return keys

0.7.3
=====
- DEPATISnet integration: more fixes

0.7.2
=====
- DEPATISnet integration: minor fixes

0.7.1
=====
- ui, middleware: proper DEPATISnet integration
- cache search queries for one hour

0.7.0
=====
- search at DPMA DEPATISnet: prototype
- ui: highlight "bi" search terms in abstract

0.6.7
=====
- fix query parameter backwards compatibility: ship_url vs. ship-url

0.6.6
=====
- fix switch to patentsearch.elmyra.de for /office urls

0.6.5
=====
- ui: drawings-carousel: request image information asynchronously to make result list display snappy again
- fix direct access url semantics in local development (hack)

0.6.4
=====
- fix direct access url semantics

0.6.3
=====
- ui: add "beta" badge to title
- ui: drawings-carousel: always request image information to display fully qualified "Drawing #1/2"
- ui: make widths of all widgets equal
- switch to patentsearch.elmyra.de
- better url semantics for direct access, e.g. /num/EP666666

0.6.2
=====
- refactor application layout on code level
- ui: refactor basket into solid marionette component
- ui: add localForage library
- ui: temporarily remove cql quick query builder helper actions
- ui: make pagination links black, not blue
- ui: fix link to CCD Viewer (upgrade from /CCD-2.0.0 to /CCD-2.0.4)
- ui: print/pdf: honor current query and pagesize

0.6.1
=====
- middleware: fix result pdf rendering by using http url instead of https

0.6.0
=====
- api: refactor dpma register jump mechanics and url
- ui: add link to CCD Viewer
- ui: enhanced pagination widget: add pagesize chooser and mechanics
- ui: separated metadata info widget from pagination widget
- ui: external link to DEPATISnet (bibliographic data)
- middleware: link to PDF to display inline, not as attachment
- ui: attempt to fix internet explorer 10, which doesn't scale the pdf icon properly
- middleware: lots of documents lack drawings, e.g. german utility documents (DE..U1) => use "docdb" format for image inquiry
- middleware: acquire first drawing from USPTO servers, if OPS lacks them
- ui: print mode layout
- middleware: export results as pdf using phantomjs

0.5.1
=====
- dev/prod: try to exclude development javascript sources from source package

0.5.0
=====
- ui: fix height-flickering of list entry when new drawing is lazy-loaded into carousel
- middleware: activate caching of generated pdf documents
- ui: make ship-mode=single-bibdata work again
- ui: integrate 3rd-party tools via iframe (parameter "embed-item-url")
- ui: query builder I: quick access to popular fields
- ui: better place for the activity spinner
- api/cql: automatically apply number normalization to "num" fields, too
- ui: query builder II: full cql field chooser
- ui: perform query when hitting hotkey "meta+return" in query form field
- ui: clipboard modifier intercepts when pasting text into empty query form field
- dev/prod: uglify main javascript resources

0.4.2
=====
- dev: fix .bumpversion.cfg

0.4.1
=====
- ui: click on document-number in header to navigate to this document
- ui: enhance pager, display active pagination entry, display current range
- ui: open drill-down links in external window
- ui: move arrow controls of carousel to bottom of image
- ui: center "Drawing #1" label below image
- ui: don't show "Drawing #1" label when there's no image
- ui: drawing carousel: show total number of drawings in status line
- dev: prepare automatic version bumping

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
