============================
elmyra.ip.access.epo CHANGES
============================

development
===========

0.41.0
======
- api: endpoint for inquiring all publication kindcodes by publication reference

0.40.1
======
- fix highlighting for descriptions from DEPATISconnect

0.40.0
======
- middleware: api endpoint for downloading a zip archive of multiple pdf documents
- ui: wire multiple pdf zip archive download
- ui: various minor improvements, some javascript refactoring
- ui/middleware: lots of minor tweaks, more icons for notifications, wording
- ui: import and share numberlist from/via clipboard

0.39.0
======
- ui: improve field autofocus behavior
- ui: switch to expert mode when receiving url parameter ?query=
- middleware: fix UserHistory.userid uniqueness

0.38.0
======
- ui: fix statusline margin
- middleware: fix path to pdftk
- ui: fix search interface behavior weirdness
- ui: medium refactoring of javascript code from main.js/core.js to components/*
- ui: refactor ops-fulltext specific code from core.js to ops.js
- middleware/ui: retrieve german fulltexts from DEPATISconnect
- ui: major refactoring of javascript code from core.js to components/*
- ui: indicate activity (spinner) while fetching document details
- middleware: run document acquisition when document fulltext details yielded no results at DEPATISconnect
- middleware: fall back to CIPO for Canadian drawings
- ui: fix snapped scrolling in Internet Explorer, improve snapping behavior in corner cases
- ui: retrieve US fulltexts from DEPATISconnect
- ui: fix Internet Explorer SVG scaling in datasource chooser
- ui: fix/improve pdf.svg
- middleware/ui: universal pdf endpoint
- middleware: record user logins with timestamp in preparation to "daily usage plan"
- ui: improve field autofocus behavior

0.37.0
======
- ui fix: query history stopped being submittable
- ui: make highlighting yellow hurt less
- ui: add header background image
- ui: refactor querybuilder initializer functions to querybuilder.js
- ui: enhance header style
- ui: refactor hotkeys code out of core.js
- ui: improve header, add link to help page
- ui: hotkeys for switching querybuilder flavor
- ui: improve querybuilder flavor event handling
- ui: print mode fixes
- ui: enhance notifications

0.36.0
======
- ui/data: properly deserialize ops response reg. nested results
- ui: compute cql query from comfort form fields already when switching tabs
- ui: query builder action button reorganization
- ui: basket action button reorganization
- ui: project action button reorganization
- ui: swap tabs: Biblio, Claims, Desc
- ui: rename “basket” to “collection”
- ui: more action button enhancements
- ui: put comment button right next to "Biblio, Claims, Desc"

0.35.0
======
- middleware: run ops search with "full-cycle" to retrieve A3 and B1 documents and more

0.34.0
======
- ui: refactor query builder to separate component
- ui: introduce field-based query builder (comfort flavor)
- ui: update cql field chooser for DEPATISnet
- ui: change font for basket display

0.33.0
======
- ui: fix patoffice integration; submit basket content without rating stars
- ui: fix broken inline links; don't propagate "datasource=depatisnet”, but explicitly switch to “datasource=ops” instead
- ui: better demo query for login panel
- auth: use session cookies instead of persistent cookies for propagating the authentication token
- auth: use "Secure" for making cookies https-only
- middleware/auth: timestamps  for User (created, modified)

0.32.0
======
- auth/identity/ui: propagate user tags to middleware, implement user create form; only permit for elmyra staff

0.31.4
======
- minor fixes and updates

0.31.3
======
- middleware: "RNG must be re-initialized after fork()" fixing again

0.31.2
======
- middleware: fix nasty "AssertionError: PID check failed. RNG must be re-initialized after fork(). Hint: Try Random.atfork()"
  error with opaque parameter subsystem

0.31.1
======
- auth/ui: tweak login form, fix cookie renewal

0.31.0
======
- auth/ui: make login screen more appealing
- auth/ui: sign out with button
- ui: permalink to current query
- auth: always permit access to “patentview” domains

0.30.0
======
- infrastructure: enable multi-site deployment
- middleware: improve serving of vanity urls vs. favicon.ico
- middleware: try to fix vanity url redirect routine
- middleware/ui: generalize patentsearch vs. patentview mechanism
- middleware/auth: nginx-lua-auth proof-of-concept (http basic auth)
- middleware/ui/auth: nginx-lua-auth enhancements (login-form)
- ui/auth: enhance login box: integrate actions (login failed, register account) via email; rumble on error
- auth: automatic cookie renewal, proper error responses for /api and /static routes
- middleware: simple user identity subsystem
- auth: authenticate against identity service, propagate userid/username to upstream service via http headers
- auth/ui: sign out with button

0.29.0
======
- middleware: make cheshire3 cql parser unicode aware
- middleware/tests: add nosetest environment
- middleware: add alternative cql parser implementation based on pyparsing, with doctests
- middleware: make pyparsing cql parser unicode aware, tweak and cleanup things
- middleware/tests: add more inline doctests to pyparsing cql parser
- middleware: make cql parser understand neighbourhood term operators
- middleware/tests: add doctests for testing DEPATISnet CQL features
- middleware/tests: add doctests for testing OPS CQL features
- middleware: fix neighborhood operator problems in value shortcut notations
- middleware/tests: add more complex, unrefurbished cql queries from the wild to depatisnet doctests
- ui: overhaul highlighting component
    - don't crash html
    - option to expand highlighting to whole words (wholeWords - false by default)
    - option to restrict highlighting to words with minimum length (minLength - undefined by default)
- middleware/tests: infrastructure for reading utf-8 encoded doctest files (from NLTK)
- middleware/tests: fix utf-8 encoding problem for doctests
- middleware: minor tweaks to cql parser
- middleware: activate new cql parser
- ui: activate new highlighting component
- middleware/caching [fix]: Beaker hashes keys with length > 250 by default which croaks when processing unicode values;
  prevent that by increasing to key_length=16384
- ui: multicolor keyword highlighting

0.28.0
======
- middleware: fix charset encoding when propagating cql query to DEPATISnet
  and extracting keywords; enhance keyword processing

0.27.0
======
- middleware: updated cheshire cql parser from upstream re. “style: PEP8 fixes for core modules”
- middleware: make cheshire cql parser smarter by allowing value shortcut notations
  like 'index=(term)' or 'index=(term1 and term2 or term3)'
- middleware: tests for value shortcut notation extension of cheshire cql parser

0.26.1
======
- ui: fix query-links in liveview mode

0.26.0
======
- ui: add "keyboarder" library
- ui: add “list-group” css from bootstrap3
- ui: add help page
- ui: add hotkey overview to help page
- ui: fix/improve inline query-link parameter building

0.25.1
======
- fix/improve build and deployment infrastructure

0.25.0
======
- ui, middleware: user-facing error messages for opaque parameter subsystem
- ui: only push url parameters to history api if they differ from their defaults
- ui: add "beta" badge again
- middleware: increase review-in-liveview link ttl to 24 hours again
- ui: fix project name display in liveview mode
- ui: enhance basket activation/deactivation in case project has no basket
- middleware: use static signing key for opaque parameter subsystem
- ui, middleware: show expiry time and improve statusline formatting in liveview mode
- ui: refactor permalink popover template
- ui: begin refactoring some global helpers to generic UiController to keep up DRY
- ui, middleware: add some generic utils
- ui: improve permalink popover widget and subsystem
- ui: basket sharing via url
- ui: basket sharing via email: improve content details
- ui: improve history api interaction

0.24.3
======
- ui: attempt to fix link expiry display

0.24.2
======
- release release

0.24.1
======
- ui, middleware: propagate metadata of signed opaque parameter token downstream to show link expiry time (ttl) in user interface

0.24.0
======
- ui, parameters: add button to popover for opening permalinks, tune urlcleaner regex
- ui: added “ZeroClipboard 2.1.2”
- ui: add button to copy permalink to clipboard

0.23.4
======
- ui, parameters: fix bootstrapping via "numberlist" query parameter

0.23.3
======
- ui: minor fix when displaying the current project name without having one
- ui: increased default opaque parameter ttl to 24 hours

0.23.2
======
- ui: attempt to fix opaque parameter mechanics for inline “query-link”s

0.23.1
======
- ui: attempt to fix permalinks re. baseurl linking

0.23.0
======
- middleware: add “translogger” to development.ini to have an access.log
- ui: clean huge url parameters like “database” or “op” from url at an early stage using the HTML5 history API to avoid referrer spam
- ui/javascript infrastructure: adapt Makefile and MANIFEST
- ui, storage: fix localforage.clear on localStorage to only wipe the current database
- middleware: add some request variables (host-, and path-information) to application configuration
- ui: make permalink buttons show popovers with full uris in text input form elements
- ui, storage: resolve “duplicate project name problem” when importing database to "context=viewer"
- ui: improve permalink mechanics
- middleware: deactivate translogger (for access.log)

0.22.2
======
- ui: add “lz-string” library
- ui: compress "data" url with "lz-string"

0.22.1
======
- ui, middleware: fix viewer lockdown mode for patentview.elmyra.de

0.22.0
======
- middleware: attempt to fix url routing re. undesired infinite redirect loops
- middleware: bind host=patentview.elmyra.de to mode=liveview and title=Patent view
- ui: interactively generate opaque permalinks
- ui: use "opaquelinks" subsystem for review-in-liveview-with-ttl permalinks

0.21.1
======
- ui, middleware: deployment aftermath fixes (setup.py dependencies, config.js woes)

0.21.0
======
- middleware, ui: "opaquelinks" subsystem on top of JSON Web Tokens
- ui: use "opaquelinks" subsystem for generating inline links in liveview mode
- ui, middleware: major parameter fiddling overhaul
- ui: enable fanstatic minified mode

0.20.1
======
- ui [fix]: don't rebuild comments everytime list gets focus
- ui, ux: improve post database wipe experience
- ui: fix document color indicator when document is just added to basket, without any score or dismiss flag set
- ui, ux: display activity indicator and permalink buttons in liveview

0.20.0
======
- ui: disable autofocus of query textarea on page load
- ui, storage: refactor database import, export, reset
- ui, storage: introduce multi-tenancy by "context" query parameter
- ui, storage: fix localForage keys() bug
- ui, storage: add jquery.base64 library
- ui, storage: add stripped-down dataurl library
- ui: make review mode available via url parameter datasource=review
- ui: improve application configuration and bootstrapping
- ui, storage: export and import database to/from "data" URL scheme, see RFC 2397
- ui: permalink button for liveview mode
- ui: propagate state of (mode, context, project, datasource=ops) into query parameters of inline links

0.19.0
======
- ui: improved application vs. project bootstrapping
- ui: improved quick notification helper
- ui, storage: database import
- ui, storage: improve backup format

0.18.0
======
- ux: make the pdf open on shift+p
- ui, storage: update backbone-relational to b8ab71a449ff (2014-06-10)
- ui, storage: presumably fix object corruption woes with localforage.backbone
- ui, storage: comments plugin, alpha, also opens on "c" key
- ui, storage: update to latest localforage 3ef964cda96 for getting an array of all keys for backup feature
- js: add Blob.js and FileSaver.js for saving files locally without user interaction
- ui, storage: database export, database wipe

0.17.0
======
- ui: color indicator for score/dismiss state
- ui: improve document header layout
- ux: improve hotkey assignments
    - right, left: navigate the tabs
    - shift+right, shift+left: navigate the drawings carousel
    - p: open the ops pdf
    - shift+e, shift+d: open espacenet re. depatisnet
    - alt+shift+e, alt+shift+d: open epo register re. dpma register
    - shift+c: open ccd viewer

0.16.1
======
- ui: fix "review" regression
- ui: rename OPS => EPO, DEPATISnet => DPMA, adapt hotkeys
- ui: improve rating:
    - get rid of "added, but not rated" state
    - get rid of "plus" button, just leave "trash" button for removing an item
- ux: improve hotkey assignments
- ui: improve document header layout
- ui: improve rating widget layout

0.16.0
======
- ux: new quick- and vanity urls
    - /publicationdate/2013-03-03/2013-04-03
    - /publicationdate/2014W10
    - /today, /week, /month, /year
    - /country/us
    - /cpc/"H04B7-15542"
- ux: link to espacenet worldwide (biblio data)
- ui: add library “jQuery Raty”
- ui: “dismissible" extension to “jQuery Raty”
- ui: rating widget for BasketEntryModel
- ui, storage: add title of selected document to BasketEntryModel

0.15.0
======
- ui: add “notify.js”
- ui: improve basket, add BasketEntryModel
- ui: fix fulltext display, raw content nodes might not be lists
- ui: also record depatisnet queries, improved query recording in general
- ui: don’t use depatisnet as default datasource
- ui: fix highlighting edge case again
- ux: add jquery.viewport
- ux: hotkeys + and - for adding/removing the document in viewport to/from basket
- ux: snapped scrolling with spacebar

0.14.0
======
- attempt to fix result list pdf export
- ui: move project chooser above basket
- ui: cql history chooser

0.13.1
======
- ui: improve layout of publication date and application date
- ui: fix missing popover after switching inline detail view
- ui: disable button which shows basket entry count

0.13.0
======
- ui: don't display application number
- ui: improve header title style
- ui: improvements to basket status- and action buttons/displays
- ui: fix: citation environment links didn't propagate project context
- ui: improve style of citation environment links
- ui: improve style of priority display
- ui: improve style of highlighting
- ui: improve display of classifications
- ui, middleware: display fulltext: description and claims
- ui: proper highlighting for description and claims
- ui: "Add all" action for adding the whole page of shown documents to the basket

0.12.0
======
- limit citatory query to 10 items due to ops restriction
- ui: modify/extend citation link buttons
- ui: "new project" action
- ui: display number of entries in basket
- ui: improve classification display: add ipc and cpc classes
- ui: display priority claims
- ui: display application number

0.11.0
======
- ui: propagate project context across inline query links
- ui: share basket via email
- ui: link to citatory documents

0.10.4
======
- ui, storage: fix nasty bug with basket.remove operation

0.10.3
======
- meta: add OpenSearch description
- ui, storage: improved robustness, honor asynchronous callback flow
- ui, storage: delete project
- ui: reposition and redesign project chooser
- ui: trigger project reload when window gets focus

0.10.2
======
- ui, storage: [fix] automatically update the "project.modified" attribute when manipulating the basket

0.10.1
======
- ui: make "modified" attribute humanly readable in project chooser widget
- ui, storage: automatically update the "project.modified" attribute when manipulating the basket

0.10.0
======
- storage: update to recent localForage library
- storage: add backbone-relational library
- storage: introduce ProjectModel and ProjectCollection
- storage: introduce BasketModel linked to ProjectModel
- feature: record all queries made to the system
- feature: make the basket persistent
- ui: add date formatting library “moment.js” and helpers
- ui: add “bootstrap-editable” widget
- config change: cache searches for 6 hours
- ui, storage
  - add ProjectChooserView and accompanying mechanics
  - properly string project-/basket-relationships and -behaviors together
  - patch localforge.backbone.js to make things actually work (weird thing)

0.9.0
=====
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
- ui: add “bootbox” library
- ui: add basket share button (dummy)

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
