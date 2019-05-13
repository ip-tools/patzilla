====================
IP Navigator CHANGES
====================


Development
===========


2019-05-13 0.166.2
==================
- [ui] Improve "Fix export with non-ascii characters accidentally slipped into patent numbers"
- [mw] Fix per-vendor settings for OPS credentials


2019-05-13 0.166.1
==================
- [mw] Fix missing dependency


2019-05-13 0.166.0
==================
- [ui] Upgrade to jQuery 3.4.1
- [ui] Add "clean-webpack-plugin" to cleanup the assets folder before building
- [mw] Improve settings for having per-vendor OPS credentials
- [ui] More flexbox for header layout
- [ui] Improve comment editing usability


2019-05-08 0.165.0
==================
- Fix broken "nasa-public-domain" demo link. Thanks, Andrii!
- Adjust DEPATISnet data source adapter to upstream changes. Thanks, Gaby!
- Fix export with non-ascii characters accidentally slipped into patent numbers. Thanks, Andreas!
- Improve styling capabilities
- Remove defunct upstream database
- Add ``patview`` to the list of accepted patentview subdomains


2019-03-09 0.164.1
==================
- Fix/improve Makefile and inline doctests
- Fix DPMAregister data source


2019-03-05 0.164.0
==================
- [doc] Update documentation
- [mw] Allow access to /ping endpoint
- [mw] Fix minor regression
- [mw] Fix tests
- [mw] Resolve issue when European publication server returns
  reference to WIPO as HTML response instead of PDF document
- [mw] Pad document numbers for granted patents to 8 digits
  with leading zeros when accessing USPTO for PDF documents
- [mw] Try USPTO servers before DPMA servers when accessing PDF documents
- [mw] Deduplicate results with "family member by priority" feature


2019-02-21 0.163.0
==================
- [mw] Use EPO publication server for obtaining PDFs of EP publications (#12). Thanks, Felix!
- [mw] Use USPTO publication servers for obtaining PDFs of US documents
- [mw] Improve generic PDF data source
- [mw] Fix "Family member by priority" functionality


2019-02-14 0.162.2
==================
- [ui] Fix opening keyword editor


2019-02-14 0.162.1
==================
- [ui] Fix feature flag evaluation
- [ui] Tune snackbar position, padding and colors based on ambient


2019-02-13 0.162.0
==================
- [ui] Gradually ramping up ES6
- [ui] Notify users by MDC Snackbar, ditch NotificationFx
- [ui] Compute effective full text data source by honoring its definition order. Thanks, Felix!
- [ui] Add Material Design Icons
- [ui] Improve MDC dependency chain
- [ui] Improve stack subsystem
- [env] Improve Docker setup. Thanks, Felix!
- [mw] Minor fix re. query expression parsing
- [env] Add notes about troubleshooting sandbox installation problems
- [env] Add basic Vagrantfile
- [ui] Adapt to renaming the font-awesome package dependency
- [mw] Switch to `python-epo-ops-client`_ for accessing OPS.
  Thanks Martin for reporting this glitch and thanks George for conceiving this fine Python package.
- [ui] Add link to New Espacenet, see #4. Thanks, Felix!
- [ui] Attempt to mitigate "TypeError: t is null" notifications from production
- [ui] Fix crawler dialog
- [ui] Fix export dialog
- [mw] Trim verboseness when not having DEPATISconnect enabled
- [mw] Fix and improve data export


.. _python-epo-ops-client: https://pypi.org/project/python-epo-ops-client/


2018-11-26 0.161.1
==================
- [ui] Add missing ``get_unique_key`` method on ``GenericExchangeDocument`` placeholder items


2018-11-26 0.161.0
==================
- [ui] Make IssueReporter work on dev and prod equally good
- [ui] Improve Stack subsystem mechanics
- [ui] Improve logging and debugging
- [ui] Add ApplicationProfile subsystem
- [ui] Improve Stack subsystem data model
- [ui] Improve jQuery3 compatibility
- [ui] Improve INID code labels, refactoring
- [ui] Add display flavour with verbose INID code labels
- [ui] Add a few Material Design Components
- [ui] Add Stack opener button


2018-11-23 0.160.0
==================
- [ui] Bump wording
- [ui] Fix conditional menu item display
- [ui] Improve design and positioning of menu opener
- [ui] Refactor main application CSS
- [ui,mw] Refactor vendor-specific feature flags
- [ui] Redesign document header with CSS Flexbox and CSS Grid Layout
- [ui] Fix inline linking to application document with DOCDB number
- [ui] Fix hotkey event handling
- [ui] Link to CCD version 2.1.8
- [ui] Add action for expanding comment panels of all documents
- [ui] Introduce Stack subsystem


2018-11-20 0.159.0
==================
- [ui] Fix comfort form zoom text width
- [ui] Fix z-index for sticky header
- [ui] Improve comfort form layout details
- [ui] Improve project and basket controls layout
- [ui] Improve pagination widget layout
- [ui] Enable menu in wide header again
- [ui] Improve query action buttons layout
- [ui] Fix wrapping of document action buttons
- [ui] Adjust user notification message box position for wide header
- [ui] Add custom data sources
- [ui] Improve theming for search action button
- [ui] Add stub for custom export variant


2018-11-16 0.158.0
==================
- [ui] Improve responsiveness of query builder and its widgets


2018-11-15 0.157.0
==================
- [ui] Add grid content variant


2018-11-14 0.156.1
==================
- [ui] Fix header layout


2018-11-14 0.156.0
==================
- [ui] Add wide header variant


2018-10-24 0.155.1
==================
- [ui] Fix regression re. query-link propagation when following cited documents


2018-10-13 0.155.0
==================
- [mw] Improve DEPAROM query expression syntax handling
- [ui] Simplify header layout by using CSS Flexbox


2018-10-12 0.154.0
==================
- [ui] Fix occasional cropped display of drawings
- [ui] Prepare drawings loader for fetching new items when navigating to previous item
- [ui] Reorder comfort form fields again
- [ui] Nail Javascript module dependencies to exact versions
- [mw] Fix error reporting and logging issues
- [ui] Hide previous/next drawing navigation buttons when displaying a single drawing
- [ui] Prevent out of bounds navigation to the previous drawing if there's just one item in the collection


2018-10-08 0.153.0
==================
- [mw] Don't run Ikofax expression through CQL parser
- [ui] Fix error propagation
- [ui] Signal search syntax in search history entry
- [mw] Allow Ikofax syntax from URLs, e.g. ``?datasource=depatisnet&query=ikofax:EP666666%2Fpn``
- [ui] Refactor syntax chooser data model
- [ui] Properly propagate Ikofax mode to Liveview mode
- [ui] Improve "Share this search" dialog
- [ui] Disable dummy exception catcher introduced accidentally when migration to jQuery3
- [ui] Fix rendering in quick access mode, e.g. ``/view/pn/EP0666666``
- [ui] Improve usability of "Share this search" and "Fetch result numbers" in the context of search results
- [mw] Fix "List of publication numbers" with Ikofax searches
- [ui] Reset search modifiers when recalling a search from history
- [ui] Reset Ikofax mode when using comfort form again
- [ui] Fix inline "query-link" mechanics
- [ui] Improve dirty signalling for comfort form
- [ui,mw] Add fields "application date" and "priority date" to comfort form
- [ui] Improve querybuilder responsiveness
- [mw] Improve date parsing for query expression translator
- [ui] Better demo values for new comfort form fields "appdate" and "priodate"
- [ui] Search by kindcode through comfort form at DEPATISnet


2018-09-28 0.152.0
==================
- Exclude .DS_Store files from the release tarball
- [mw] Fix Umlaut issues with DEPATISnet. Thanks, Martin!
- [mw] Strip DEPATISnet query expression before propagating to upstream. Thanks, Martin!
- [mw] Grok error messages from erroneous DEPATISnet queries
- [ui] Add new universal "start_search" method for kicking off a blank-slate search action
- [ui] Run boot-time search after activating basket model
- [ui] Limit query expression syntax chooser to DEPATISnet only
- [ui] Adjust field name chooser for Ikofax syntax
- [mw] Compute keywords from Ikofax expression (quick solution)


2018-09-26 0.151.0
==================
- Add status endpoints for monitoring upstream services
- Honor tag "login:disabled" on authentication
- Add multi-tenant email address and content configuration
- [ui] Upgrade to webpack v4
- [ui] Fix Javascript source maps
- [ui] Upgrade to jQuery 3.3.1, modernizr 3.6.0, moment 2.22.1, select2 3.5.1, url-join 2.0.5 and waypoints 4.0.1
- [ui] Use Babel loader for webpack
- [doc] Improve installation documentation
- [mw] Direct access to OPS 3.1 API has been disabled, so stop linking to it
- [ui] Fix: When creating new project, convert project name to string
- [mw] Improve DpmaRegisterAccess re. language selection
- [mw] Improve image conversion by using the Pillow library
- [mw] Improve downtime signalling for EPO OPS API
- [mw] Improve report generation with ``unoconv``
- [license] Officially upgrade to EUPL 1.2
- [ui] Improve full text display for IFI CLAIMS
- [mw] Fix full text acquisition from Espacenet
- [ui] jQuery 3.x upgrade aftermath:

    - Migration fixes
    - Upgrade packages bootbox, jq-pagination, jquery.viewport and stacktrace-js
    - Use clipboard.js instead of ZeroClipboard

- [ui,mw] Refactor, improve and modularize data source adapter interfaces
- [ui] Add timestamp to error report
- [ui] Fix display of query builder sorting state
- [mw] Reenable response caching for IFI CLAIMS API
- [ui] Use "cheap-source-map" strategy with webpack to fix error handling with Chrome
- [mw,ui] Add improved data source adapter for SIP again
- [mw] Unlock DEPAROM Query Translator from MTC depa.tech API
- [mw] Fix development mode re. missing display of data source chooser
- [ui,mw] Add basic Ikofax expression support for searching at DPMA DEPATISnet
- [ui] Move logout link to the bottom of the menu

2018-03-17 0.150.0
==================
- Honor tag "email:invalid" for "list emails" endpoint
- Improve location of general notification box
- Improve user experience for "import database"

2018-03-16 0.149.0
==================
- Upgrade to MechanicalSoup 0.10.0. Thanks, Matthieu and Dan!
- Improve whitelabel capabilities
- Improve error response handling for IFI CLAIMS
- Set default language for "dpmaregister" crawler to English
- Improve confirm dialogs for database "wipe" and "import" actions
- Improve whitespace handling at query expression translation time. Thanks, Luca!

2018-01-22 0.148.1
==================
- Fix DPMAregister crawler

2018-01-19 0.148.0
==================
- DPMAregister crawler: Use improvements from MechanicalSoup==1.0.0-dev. Thanks, Matthieu!
- DPMAregister crawler: Acquisition of localized artefacts (language en vs. de)

2018-01-02 0.147.1
==================
- Fix decoding of DPMAregister "pct-or-regional-{publishing,filing}-data" for list representations

2018-01-02 0.147.0
==================
- Add HTTP interface to DPMAregister data

2017-12-19 0.146.0
==================
- Some updates to the DPMAregister access library. Thanks, Felix!

    - Get DPMA register URL for DE documents by calculating the checksum of the document number
    - Remove country code for DE Aktenzeichen inquiry
    - Change baseurl to use https

- More updates to the DPMAregister access library.

    - Fix access by honoring throttling employed by DPMA
    - Refactor and improve library API and inline documentation
    - Provide new access methods ``fetch_st36xml`` and ``fetch_pdf``
    - Switch scraper from "mechanize" to "MechanicalSoup"
    - Provide command line interface program ``dpmaregister``
    - Introduce response caching with a TTL of 24 hours
    - Decode ST.36 XML documents to JSON
    - [ui] Fix direct link to DPMAregister

- Upgrade to Moment.js 2.20.0 re. CVE-2016-4055

2017-11-16 0.145.0
==================
- [cmd] Add ``patzilla-user import`` command for importing users from CSV file, see also :ref:`user-import`.

2017-11-16 0.144.0
==================
- [cmd] Add ``patzilla-user add`` command for adding users to the database, see also :ref:`user-add`.

2017-11-15 0.143.2
==================
- [ui] Fix leaking of templateHelpers variables into model attributes
- [ui] Fix export woes after switching between projects

2017-10-31 0.143.1
==================
- Documentation: Overall improvements and polishing

2017-10-31 0.143.0
==================
- Add console interface program ``patzilla``
- Add command ``patzilla make-config {development,production}`` for generating a configuration file template
- Improve documentation

2017-10-31 0.142.5
==================
- Fix MANIFEST.in
- Update fabfile and documentation regarding installation from PyPI

2017-10-31 0.142.4
==================
- Attempt to fix README
- Make Makefile not commit itself when minifying urlcleaner.js

2017-10-31 0.142.3
==================
- Fix numberlist search in opaque parameter mode for patentview domains
- Fix Makefile
- Naming things
- Add NASA public domain demo to README

2017-10-31 0.142.2
==================
- Improve release process, upload to PyPI

2017-10-31 0.142.1
==================
- Update documentation and infrastructure

2017-10-25 0.142.0
==================
- Add Sphinx documentation infrastructure and skeleton
- Fix search metadata reset behavior
- Activate IssueReporter email target again
- Update IFI CLAIMS documentation
- Fix dependencies in setup.py for compatibility between Mac OSX and Debian GNU/Linux
- Backward compatibility for datasource identifier in user enablement settings
- Fix error when opening export dialog after creating new project. Thanks, Benjamin!
- Account for DEPATISnet responding with US application publication numbers
  with leading zeros after country code, e.g. US020170285092A1

2017-10-13 0.141.0
==================
- Enable display of "CPCNO" classifications
- IFI CLAIMS fulltext fixes and improvements

    - Add proper escaping and newline replacement for description, e.g. KR20170103976A
    - Description sections “industrial-applicability” and “reference-signs-list” were missing, e.g. KR20170103976A
    - Update claims structure, e.g. JP2017128728A
    - Update "description-of-drawings" description section, e.g. JP2017128728A
    - Parse "chemistry" and other figref nodes in "summary-of-invention.tech-solution" section, e.g. JP2017128728A
    - Description section "description-of-embodiments.embodiments-example" was missing, e.g. JP2017128728A

2017-10-12 0.140.2
==================
- Fix drilldown capabilities in liveview mode
- Fix liveview mode when running on localhost
- Fix pagesize chooser reset behavior

2017-10-12 0.140.1
==================
- Improve patentview domain handling
- Update demo query just before expiration

2017-10-12 0.140.0
==================
- Improve command line access to data sources
- Improve auxiliary tools selection for “convert” and “pdftk”
- Fix multivendor “hostname_matches” selection
- Fix User data model
- Fix segfaults with lxml on Debian Wheezy (7.11)
- Update production setup documentation

2017-10-12 0.139.7
==================
- Fix “result-count-total” formatting - once more

2017-10-12 0.139.6
==================
- Fix “result-count-total” formatting

2017-10-12 0.139.5
==================
- Attempt to fix “result-count-total” formatting
- Bring tooling for production setup up to speed

2017-10-11 0.139.4
==================
- Fix: Number normalization for DE..T1 documents didn't match expectations of OPS 3.2
- Improve and harmonize command line access to data sources

2017-10-11 0.139.3
==================
- Fix typo in setup.py
- Improve texts re. whitelabeling
- Fix: Daterange "within" query stopped working after upgrade to OPS 3.2
- Fix: Paging stopped working in review mode

2017-10-11 0.139.2
==================
- Fix citations display problem for document US9674560B1
- Slightly improve NPL citations display

2017-10-11 0.139.1
==================
- Add utility routine for purging seen numbers to database tool
- Fix database wipe confirm dialog
- Project delete should account for child BasketEntry entities

2017-10-11 0.139.0
==================
- Get rid of more static html templates and refactor to javascript application
- Fix image loading for jQuery Raty
- Harmonize help subsystem
- Reconfigure navigator url and main application entrypoints
- Fix “user create” widget
- Use vanilla or slightly patched components from upstream:
  jqPagination, KeyBoarder, notificationFx, jquery-hotkeys, lz-string

2017-10-09 0.138.0
==================
- Update configuration file templates re. vendoring
- Load HTML templates using webpack's "underscore-template-loader"
- Large Javascript refactoring, improve directory layout and
  modularization contexts for all auxiliary application components
- Add stylesheet to default vendor (patzilla)
- Harmonize conditional datasource enablement
- Refactor frontend components to new directory layout

    - Data source adapters
    - Application layout- and error templates
    - Result list and document details
    - Family details
    - 3rd-party libraries and widgets
    - Application core

2017-10-06 0.137.0
==================
- Fix opaquelinks subsystem
- Fix exception when crawling without criteria
- Vendor MTC: Update product name to “depa.tech navigator"
- Use jquery.redirect from npmjs.com
- Use jquery.viewport from npmjs.com
- IFI CLAIMS: Improve description fulltext display re.
  section “advantageous effects” (missing), embedded lists and embedded drawings
- Improve handling of global and runtime configuration settings
- Add vendor branding assets as discrete css stylesheets

2017-09-15 0.136.0
==================
- Fix: Don’t cache “404 Not Found” responses from OPS' image inquiry API
- Fix hard errors in the aftermath of repository cleanup
- Improve exception handling for authentication errors against OPS API
- Improve datasource configuration mechanics
- Improve OPS API error propagation
- Update documentation re. database sandbox mode
- Pull application-wide upstream API authentication credentials from datasource settings
- Trim down automatic user provisioning
- Application configuration file cleanup
- Large namespace refactoring
- Make tests work again
- Properly handle and propagate cache database connection errors
- Disable automatic "admin" user provisioning
- Documentation, “naming things” and further cleansing
- Naming things: Rename HTTP header for transporting the keywords
- Improve parsing robustness and error propagation on invalid “pubdate” fields
- Be graceful on officelink hotkey selection problems
- Improve header layout in liveview mode
- Upgrade to most recent versions of Python foundation modules across the board
- OPS stopped delivering the elapsed time when crawling
- Improve basket model and interaction sanity
- Database export filename: naming things
- Introduce webpack for bundling the Javascript/CSS assets
- Mangle Javascript code into a suitable form for being webpacked
- Fix test framework
- Update claims fulltext manipulation for DEPATISconnect
- Introduce component activation conditionals and improve wording
- Improve fulltext display re. OPS API 3.2 changes
- Reduce notification popup display time from six to four seconds
- Introduce webpacked version of login.js
- Fix redirect on failed logins
- Protect sensible configuration settings from leaking into javascript environment
- Use vendor information from application settings
- Refactor development mode flag
- Release packaging wrt webpack
- Improve vendor information handling

2017-09-08 0.135.0
==================
- Update IFI CLAIMS API endpoint
- Use [OL] prefix for displaying titles without @lang attribute
- Fix online help link in menu
- Fix issue reporter for query transformation
- Refactor per-datasource max_hits mechanics
- Fix behavior when reviewing empty basket
- Add datasource depa.tech
- Add branding for vendor MTC
- Improve number normalization around datasource IFI CLAIMS
- Fix document cycle sorting
- Fix highlighting for Solr complexphrase expressions
- depa.tech: Also search for priority number when using “Number” field in comfort search
- depa.tech: Populate field symbol chooser for expert search
- Bring list of global office links up to speed
- Display both (docdb) and (epodoc) numbers at application reference
- depa.tech: Highlighting for expert search
- Use recent browser-like User-Agent across the board
- Improve patent number normalization and usage
- Improve Espacenet screen scraper
- Migrate to OPS API version 3.2
- Improve/fix patent display after OPS 3.2 migration

2017-04-06 0.134.1
==================
- Improve search backend error handling and display

2017-04-05 0.134.0
==================
- Minor improvement to basket.add(…) method
- Fix IFI CLAIMS anomaly: KR20170037210A has "name" instead of "last-name" in applicants node
- Also grok “image/jpeg” as source format from IFI CLAIMS for delivering single pages and drawings
- Enable caching for IFI CLAIMS media downloads

2017-04-04 0.133.0
==================
- Fix parties (applicants, inventors) display for IFI CLAIMS: An error occurred when displaying the document 'IN268402B’. Thanks, Benjamin!
- Fix exception flood from basket model
- Fix basket “Add visible” feature
- Properly handle errors when IFI CLAIMS delivers empty document for bibliographic data, e.g. IN268402A
- Make IFI CLAIMS data model grok patent citations
- Enable documents from office “KR” for IFI CLAIMS bibliographic data interface
- Improve language priorization for fulltexts from IFI CLAIMS: EN, DE, others
- Add datasource label to fulltext sections

2017-03-28 0.132.3
==================
- Improve/fix IFI CLAIMS data model implementation
- Add “CN” to list of countries where bibliographic data can be acquired from IFI CLAIMS
- Add datasource label to detail view

2017-03-28 0.132.2
==================
- Attempt to fix bibliographic model implementation again

2017-03-28 0.132.1
==================
- Fix bibliographic model implementations

2017-03-28 0.132.0
==================
- Improve fulltext/claims display for RU2015121704A via IFI CLAIMS
- Refactor bibliographic model implementation
- Optionally display bibliographic data from IFI CLAIMS (e.g. IN2015CH00356A)

2017-03-10 0.131.0
==================
- Improve logging and error handling
- Enable fulltext acquisition for countries BE, CA, CN, FR, GB, JP, KR, LU, NL, RU through IFI CLAIMS

2017-03-08 0.130.3
==================
- Update IFI CLAIMS documentation re. combined {!complexphrase} expressions
- Improve IFI CLAIMS translation re. queries with {!complexphrase} fulltext criteria

2017-03-08 0.130.2
==================
- Fix numberlist crawling after distinguishing between query expression and query filter parameters

2017-03-07 0.130.1
==================
- Minor fix to allow exporting of projects with “seen only” documents

2017-03-07 0.130.0
==================
- Bugfix re. bad assignment between “seen” and “rated” documents in basket model
- Switch to interface flavor “expert” when signalling through url parameter “mode=expert”
- IFI CLAIMS: Distinguish between query expression and query filter parameters to better support certain time range searches

2017-03-03 0.129.1
==================
- Fix support email delivery
- Fix deployment

2017-03-02 0.129.0
==================
- IFI CLAIMS: Properly respond to “no servers hosting shard” error messages
- IFI CLAIMS: Improve keyword highlighting
- Improve error handling
- Keyword highlighting: Switch from whole words to fragments
- Improve support- and system-email machinery
- Move support email body template from code to configuration
- Also add user as recipient for support emails

2017-02-27 0.128.2
==================
- Improve datetime and fulltext parsing for IFI CLAIMS

2017-02-27 0.128.1
==================
- Improve IFI CLAIMS interface and documentation re. “maxClauseCount is set to …” error messages

2017-02-22 0.128.0
==================
- Update IFI CLAIMS documentation
- Add vendor branding for Europatent

2017-02-20 0.127.0
==================
- Fix typo in IFI CLAIMS documentation
- Disable data source “FulltextPRO”

2017-02-20 0.126.2
==================
- Fix date parsing for full 4-digit years with IFI CLAIMS

2017-02-20 0.126.1
==================
- Fix parsing regular ISO dates with IFI CLAIMS

2017-02-20 0.126.0
==================
- Update branding for vendor Europatent
- IFI CLAIMS: Add handbook and fix field name chooser
- Make comfort search at IFI CLAIMS accept date expressions in german format

2016-11-15 0.125.3
==================
- Tune branding for patselect.ip-tools.io

2016-11-15 0.125.2
==================
- Tune branding for patentview.ip-tools.io

2016-11-15 0.125.1
==================
- Tune multi-vendor branding

2016-11-15 0.125.0
==================
- First version of multi-vendor branding

2016-11-13 0.124.0
==================
- Improve interactive DEPATISconnect behavior through fastpath document retrieval and acquisition
- Fix Espacenet fulltext retrieval fallback
- Improve "FulltextPRO" error handling

2016-10-26 0.123.1
==================
- Fix logging error on "FulltextPRO" exception

2016-10-18 0.123.0
==================
- Fix placeholder display re. WO2001000469A1 vs. WO0100469A1
- Fix setup woes re. setuptools>=11.3 dependency
- Reduce production search cache time to 2 hours
- Catch new type of "FulltextPRO" error
- Improve layout of search modifiers "Family member by priority" and "Remove family members"

2016-10-12 0.122.0
==================
- Improve anonymization of sensitive user information re. issue reporter
- Improve patent number normalization support for EAPO numbers (Eurasian Patent Organization), e.g. EA21949B1
- [TAG] Staging milestone

2016-10-12 0.121.0
==================
- Improve swapping of family members by priority: DE, EP..B, WO, EP..A2, EP..A3, EP, US

2016-10-11 0.120.2
==================
- Fix biblio inquiry for family member swapping
- Fix drawing display of CA industrial design documents

2016-10-11 0.120.1
==================
- Fix priority swapping for data source DPMA and FulltextPRO
- Fix query recording re. timing problems

2016-10-10 0.120.0
==================
- Fix DEPATISnet client re. form field "DocId"
- Fix unoconv export re. HOME environment variable
- Swapping of family members by priority DE, EP, WO, US
- Improve FulltextPRO downtime message
- Use wide layout for user interface
- Allow rotating of drawings
- Fix liveview mode when exporting a large number of basket items re. "op" parameter url cleaning
- Introduce new cache area “longer” (1 week) for caching PNG drawings
- Enable caching of static assets for 1 hour again
- Use Marionette and Underscore templates for the basic application layout (header, content, footer)
- Improve application bootstrapping behavior
- Improve application boostrapping: configuration vs. theme. Work towards a white-label version.
- Attempt to fix to errors reported by issue reporter

2016-08-07 0.119.6
==================
- Another attempt to fix liveview mode: Strip "op" parameter before computing drilldown opaque URLs.

2016-08-07 0.119.5
==================
- Attempt to fix liveview mode: Original "op" parameter was propagated without honoring clicked elements.

2016-08-06 0.119.4
==================
- Fix ZeroClipboard by adding missing ``*.swf`` files to python package

2016-08-06 0.119.3
==================
- Improve embedded rendering

2016-08-06 0.119.2
==================
- More fixes for proper url generation to patentview

2016-08-06 0.119.1
==================
- Improve OPS logging
- Fix liveview link propagation

2016-08-06 0.119.0
==================
- Depend on more recent versions of Python modules (pyOpenSSL, pyasn1, ndg-httpsclient) to ensure SNI compatibility for egress HTTP requests
- Improve embedding of single documents for Workbook exports

2016-08-05 0.118.0
==================
- Improve efficiency when accessing PDF archive: Use persistent requests session, use requests transport
  with xmlrpclib, switch API entrypoint at upstream data provider to improved Linux infrastructure
- Try to improve TIFF to PNG conversion quality (contrast) by switching to more recent version of ImageMagick
  - Before: https://patentsearch.elmyra.de/api/drawing/BE1018034A6?page=2
  - After: https://patentsearch-develop.elmyra.de/api/drawing/BE1018034A6?page=2
- React appropriately to “busy” or “overload” situations at OPS by introducing little amounts of delays in request processing
- Improve robustness and logging on multi-stage fetching of PDF documents
- Improve data export robustness and logging

2016-08-04 0.117.0
==================
- Improve robustness of OPS OAuth client
- Add Javascript components “jQuery Redirect” and “bootstrap-slider”
- Improve data export facility and user interface
- Add Python modules pandas, XlsxWriter and html2text
- Add XML Workbook to PDF conversion based on LibreOffice, unoconv and envoy

2016-05-11 0.116.4
==================
- Fix logic for displaying per-user-enabled data source buttons
- [TAG] Staging milestone

2016-05-02 0.116.3
==================
- Fix another Javascript runtime error reported by issue reporter on staging
  re. old query history items vs. new search modifiers

2016-05-02 0.116.2
==================
- Fix some Javascript runtime errors reported by issue reporter on staging

2016-05-02 0.116.1
==================
- Issue reporter: Fix query expression to user interface propagation, for “no results” panel as well as the issue reporter dialog


2016-05-01 0.116.0
==================

Features
--------
- IFI: Enable expression parsing with “Class” criteria in comfort form
- IFI: Remove family members
- IFI: Basic crawler
- CIPO: Add direkt link to CIPO, the Canadian Intellectual Property Office
- WIPO: Add direkt link to WIPO, the World Intellectual Property Office
- DPMA: Adapt wildcard semantics in comfort form to world standards
- Query builder: Improve design and layout of history chooser
- Display: For EP..A4 documents, display drawings of family members
- Display: Improve experience with brand new US documents not yet in OPS, Espacenet or other databases, e.g. US9317610B2

    - If PDF can not be acquired elsewhere, redirect to USPTO servers
    - If drawing actually gets loaded despite the document having no bibliographic information,
      swap out the placeholder and display the drawing at least. Also improve feedback to the user.
    - Add external links to USPTO for US documents
    - Improve display of drawing "totalcount" value if there's no information about it


Infrastructure
--------------
- Generalize keyword field whitelist handling between OPS and DEPATISnet
- Generalize query expression parsing between CQL (EPO, DEPATISnet) and Solr (IFI CLAIMS)

    - IFI: Improve keyword extraction and highlighting
    - IFI: Improve class rewriting in comfort form
    - IFI: Roundtrip class rewriting for proper keyword extraction from query expression
    - IFI: Basic software tests for query expression parsing

- Add caching for drawings from USPTO and CIPO
- UI: Improve error handling for batch requests
- Use generic DatasourceCrawler also when doing batch requests to OPS to gain generic filtering routines
- Improve image/pdf acquisition robustness
- Improve user interface wording for placeholders and more
- Enhance bulk request error handling
- IFI: Propagate information about removal of patent family members from middleware to frontend
- Improve placeholders for feature “Remove family members”
- “Report problem” subsystem and user interface
- Display: Introduce mini menu
- Unify response data- and error-channels amongst all data sources
- Add commandline tool for cleaning the IP Suite Navigator Browser database
- Streamline Javascript application boot process
- Improve search modifier propagation: Add pathway from query parameters to metadata


Bug fixes and minor updates
---------------------------
- Improve OPS connection error handling
- Improve keyword extraction and propagation
- Fix woes with javascript “htmlentities” machinery
- LinkMaker: Update/fix urls for Espacenet and Google
- Improve wording on email for "Document unavailable » Report problem"
- Don’t quote single numbers for OPS query expression in “perform_listsearch”
- Improve document number decoder: Make it grok JP numbers like “JPWO2013186910A1”
- Fix sorting of documents in subsearch- and numberlist-modes
- Deactivate downvoting EP..A3 documents when displaying most recent publication
- Stop saving reference to project in QueryModel, this has led to dereferenced ProjectModel objects sucking up localStorage space
- Fix pager setup on numberlistsearch
- Fix family member removal notification: Differentiate between empty results from OPS in general and empty results after slicing
- Don’t use review mode when sharing a basket via link as numberlist
- Don’t display menu entrypoint in “liveview” mode


2016-04-18 0.115.0
==================
- Don’t use DE..A8 family members as alternative for displaying drawings
- Use alternatives from patent family also when displaying drawings of DE..A8 documents

2016-04-18 0.114.0
==================
- Improve exception handling for "FulltextPRO" upstream
- Update "FulltextPRO" database search endpoint after server changeover
- Improve OPS drawing inquiry re. US amendments/corrections
- Improve "FulltextPRO" session management for error cases
- Improve placeholders re. gracefulness to WO anomalies like WO2003049775A2 vs. WO03049775A2
- Improve drawings carousel by using drawings from family members for references (Aktenzeichen) like DE112013003369A5
- Reactivate SDP data adapter as IFI CLAIMS

2016-03-19 0.113.0
==================
- ui: compensate for anomaly with references-cited at EP2479266A1

2016-02-19 0.112.0
==================
- middleware: improve logging for FulltextPRO
- ui: strip kindcodes from numbers in numberlist

2016-01-06 0.111.2
==================
- "FulltextPRO" adapter: don’t decode xml from utf-8 when pretty printing
- middleware: adapt tests to changes in US number normalization
- middleware: reactivate SE..A to SE..L rewriting with number normalization

2016-01-05 0.111.1
==================
- reflect year change in copyright footers - happy new year!

2015-12-31 0.111.0
==================
- middleware: improve parsing behavior for cql micro expressions regarding discrete years in half-bounded intervals

2015-12-30 0.110.0
==================
- ui: stop storing "title" attributes into BasketEntryModel objects, also remove when touching objects
- middleware: add tool "browser_database_tool" for manipulating browser database dumps (json)
- middleware: don’t list email addresses for newsletter if user is tagged with “newsletter:opt-out”
- ui: improve display when no classifications are available
- ui: citation references from non-US family members
- middleware: add cache region “medium” with ttl of one day, set ttl of region “static” to one month (before: one year)
- middleware: improve DRAWINGS decoding from OPS image inquiry response, has great impacts on US drawings display

2015-12-22 0.109.2
==================
- ui: make IE11 behave
- ui: change color of reading progress indicator to more decent turquoise

2015-12-22 0.109.1
==================
- middleware: improve depatisnet client by vaporizing after any http error
- ui: improve reading progress indicator

2015-12-22 0.109.0
==================
- ui: add “ToProgress” top bar library
- ui: add reading progress indicator

2015-12-21 0.108.1
==================
- ui: refactor components due to import order woes

2015-12-21 0.108.0
==================
- ui: Feature "Fetch publication numbers of all results, strip kindcodes and build list of unique entries."
- ui: add jquery.waypoints library
- ui: Feature "track seen documents": introduce “seen” attribute to BasketEntryModel
- ui: Feature "track seen documents": apply basket item “seen” state to user interface by decreasing opacity of document panels
- ui: fix document list comparator re. document numbers w/o kindcode
- ui: Feature "track seen documents": introduce “mode_fade_seen” attribute to ProjectModel and bind mode behavior to it
- ui: make datasource “numberlist” and review mode honor “full-cycle” search modifier
- ui: sophisticated placeholder subsystem
- middleware: improve number normalization for US numbers, e.g. US20150322651A1
- ui: proper sorting (recent first, past first) for kindcode variants with EP..A3 downvoting
- middleware: disable long-term caching for ops family queries

2015-12-18 0.107.0
==================
- DEPATISnet adapter: fix scraper response handling re. parsing of upstream errors and result count
- DEPATISnet adapter: feature “family-replace”
- ui: fix result comparator sorting for numberlists without patent kindcodes

2015-12-16 0.106.0
==================
- middleware: allow cache invalidation for upstream resources by url parameter “invalidate=true”

2015-12-15 0.105.0
==================
- ui: display results in the same order as coming from upstream; this applies to DEPATISnet, "FulltextPRO" and Numberlist queries

2015-12-15 0.104.2
==================
- ui: improve visibility of active search option modifier buttons (full cycle, remove family members, full family)

2015-12-15 0.104.1
==================
- DEPATISnet adapter: Properly propagate search options (Modifiers, Sorting) to crawler subsystem

2015-12-15 0.104.0
==================
- DEPATISnet adapter: Feature "Sorting of results"

2015-12-14 0.103.0
==================
- FulltextPRO adapter: Feature "Full family"

2015-12-14 0.102.1
==================
- “Remove family members” at DEPATISnet: fix edge case where hit count
  would display wrong numbers when requesting in family-only mode and
  having more than 1000 results

2015-12-14 0.102.0
==================
- DEPATISnet adapter: Feature "Remove family members"
- ui: improve querybuilder layout and mechanics

2015-09-25 0.101.1
==================
- "FulltextPRO" adapter: fix xml query building re. xml declaration

2015-09-25 0.101.0
==================
- middleware: improve ops image inquiry robustness
- ui: improve numberlist robustness, filter empty entries
- middleware: improve sdp backend, fetch single resources (xml, json, pdf, tif, png)
- auth: improve lua layer robustness
- auth: turn on open access to “kindcodes” api again
- middleware: improve sdp backend, fetch multiple resources (xml:pretty,json:pretty,png,pdf)
- DEPATISnet adapter: improve error detection on upstream result decoding errors
- DEPATISnet adapter: fix XLS decoding error, upstream added new status line to first row
  e.g. "Search query: pn=(EP666666) Status: 25.09.2015"

2015-09-02 0.100.0
==================
- middleware: add flexibility to work against a local archive service instance for accessing DEPATISconnect
- middleware: improve number normalization for JP and SE documents
- middleware: improve fulltext access robustness at DEPATISconnect vs. Espacenet

2015-07-16 0.99.0
=================
- middleware: add datasource "SDP": Serviva Data Proxy / IFI CLAIMS

2015-06-02 0.98.0
=================
- middleware: smart normalization for applicant names on direct url entry

2015-05-18 0.97.10
==================
- middleware/ui: add "applicant-distinct" analytics module
- middleware: fix edge case re. proximity operators in "FulltextPRO" expressions
- middleware: DPMA register: fix form selection (don't select by name, but by number)

2015-04-10 0.97.9
=================
- middleware: fix dependency on "xlrd" for reading excel files

2015-04-10 0.97.8
=================
- middleware: switch depatisnet to data acquisition via xls (excel) file instead of csv

2015-04-09 0.97.7
=================
- middleware: fix more edge cases when parsing non-standard html entities from depatisnet csv inventor or applicant fields

2015-04-08 0.97.6
=================
- middleware: fix edge cases when parsing non-standard html entities from depatisnet csv inventor or applicant fields

2015-04-05 0.97.5
=================
- middleware: minor post-refactoring fixes

2015-03-30 0.97.4
=================
- middleware: replace html entities in csv response from depatisnet

2015-03-30 0.97.3
=================
- ui: fix "fetch result numbers" for queries including umlauts

2015-03-22 0.97.2
=================
- ui/middleware: minor fixes to embedding subsystem

2015-03-22 0.97.1
=================
- ui/middleware: make embedding subsystem more generic

2015-03-21 0.97.0
=================
- ui/middleware: standalone carousel widget

2015-03-21 0.96.1
=================
- ui: move application components

2015-03-21 0.96.0
=================
- middleware: analytics api for "newest" and "oldest" searches
- ui: preliminary access to analytics api

2015-02-26 0.95.5
=================
- middleware: fall back to Espacenet for DE- and US-fulltexts

2015-02-26 0.95.4
=================
- middleware: implement asciifolding for FulltextPRO

2015-02-26 0.95.3
=================
- middleware: fix cache key charset encoding problem by upgrading to Beaker 1.7.0dev

2015-02-25 0.95.2
=================
- middleware: fix HTTPS self-signed certificate validation problem for Python >= 2.7.9, see PEP 476
- auth: turn off open access to “kindcodes” api
- ui: fix query history display after creating new project
- ui: fix event listening when creating ProjectChooserView instances

2015-02-10 0.95.1
=================
- middleware: improve pdf bulk delivery: include report.txt into zip archive, be graceful for invalid patent numbers

2015-02-10 0.95.0
=================
- ui: fix “wipe database”
- ui: improve performance when adding many result numbers to document collection
- middleware: use MongoDB GridFS for storing large binary static resources from upstream to prevent DocumentTooLarge errors

2015-02-10 0.94.3
=================
- ui: enhance show-/hide-mechanics of paging components et al.

2015-02-10 0.94.2
=================
- middleware: fix case sensitivity problem in fulltext expression parser for FulltextPRO

2015-02-10 0.94.1
=================
- ui: fix ui lockup issues with new query history chooser

2015-01-25 0.94.0
=================
- ui: major improvements to query history subsystem

2015-01-23 0.93.3
=================
- middleware: minor but important enhancements to FulltextPRO query expression parser

2015-01-23 0.93.2
=================
- ui: fix typo in main template introduced when doing the document error template in a hurry

2015-01-23 0.93.1
=================
- ui: fix/enhance rendering of application reference and priority claims

2015-01-23 0.93.0
=================
- ui: fix display problem for documents without “patent-classification” attribute, this occurred with documents from e.g. B60N3/02, B60N3/10
- ui: display placeholder on exception in central document item template
- ui: proper page-break handling
- ui: boot application even if experiencing problems with localStorage (for print mode)
- middleware: try “wkhtmltopdf” for pdf rendering
- ui: fix display problem for documents without “classification-ipcr” attribute
- ui: enhance rendering of application reference and priority claims

2015-01-21 0.92.0
=================
- ui: offer adding all numbers to basket after fetching result numberlist

2015-01-21 0.91.0
=================
- middleware: enhance ops usage api (differentiate between "ago" and "current" - per period)
- middleware: uppercase patentnumber when searching at FulltextPRO
- ui: bug: when clicking through family citations, current view state (e.g. project) is not propagated properly
- ui: explore all family members
- middleware: more enhancements to FulltextPRO query translator
- middleware: don't use "inpadoc" field qualifier when searching for applicant or investor at FulltextPRO
- middleware: understand year ranges in comfort form, e.g. 1990-2014, 1990 - 2014, 1990-, -2014
- middleware: fix gif to tiff conversion (required for acquiring drawings from CIPO)
- middleware: username (email) should always be lowercase
- middleware: admin api: filter email addresses by tag: /api/admin/users/emails?tag=vdpm

2015-01-20 0.90.3
=================
- middleware: increase timeout for XmlRpcTimeoutServer (DEPATISconnect) from 8 to 15 seconds

2015-01-20 0.90.2
=================
- ui: distinguish between erroneous or empty responses to on-demand requests for abstracts at DEPATISconnect
- middleware: attempt to detect when searching at FulltextPRO fails due to invalid session and relogin again
- middleware: make FulltextPRO expression parser handle more expressions from the wild

2015-01-19 0.90.1
=================
- middleware: make fieldnames case insensitive at FulltextPRO expression translator
- middleware: unicode support for FulltextPRO expression translator

2015-01-19 0.90.0
=================
- ui: copy comfort form contents to clipboard, clear comfort form values

2015-01-19 0.89.1
=================
- middleware: fix keyword trimming at FulltextPRO expression converter

2015-01-19 0.89.0
=================
- middleware: major enhancements to FulltextPRO expression translator re. unqualified search expressions, tests
- middleware: enable new FulltextPRO expression translator on all inputs for fields "Class" and "Full text"

2015-01-18 0.88.1
=================
- middleware: fixes to FultextPRO expression enhancements

2015-01-18 0.88.0
=================
- middleware: enhance FulltextPRO comfort form capabilities for "Class" expressions
- middleware: enhance FulltextPRO comfort form capabilities for “Full text” expressions
- tests: tests for enhanced FulltextPRO cql expressions and parser refinements

2015-01-17 0.87.4
=================
- middleware: enhance timeout behavior at DEPATISconnect upstream

2015-01-15 0.87.3
=================
- middleware: fix "DEPATISconnect alternatives" routine

2015-01-14 0.87.2
=================
- ui: don’t display FulltextPRO query in expert mode, unless using “debug=true”
- ui: warning message re. capping the first 10 elements also should appear when exploring the citation environment in main bibliographic view

2015-01-14 0.87.1
=================
- ui: reactivate feature "Documents citing same citations"

2015-01-14 0.87.0
=================
- middleware: reverse kindcode fixing for DE documents at DEPATISconnect
- middleware: enhance patent number normalization for old US publications, e.g. US000000024087E => USRE24087E
- middleware: perform kindcode fixing also on patent normalization api
- ui: move “Fetch result numbers” button to results tool menu
- ui: deactivated feature "Documents citing same citations"
- middleware: enhance/fix FulltextPRO fulltext search field
- ui: display limits of datasource in “fetch result numbers” dialog

2015-01-13 0.86.2
=================
- middleware: enhanced patentnumber- and kindcode-normalization for offices AR, GE, IT and ES
- middleware: enhanced patentnumber- and kindcode-normalization for office DE, esp. reg. older german publications

2015-01-12 0.86.1
=================
- authentication: restrict access to admin api
- admin api: add endpoint for inquiring email addresses of all users

2015-01-12 0.86.0
=================
- middleware: FulltextPRO user impersonation / multi-tenancy

2015-01-12 0.85.0
=================
- middleware: number normalization: AT362828E should be returned as AT362828T for querying at OPS
- middleware/ui: ops upstream datasource crawler for fetching complete list of publication numbers, user interface
- ui: fix “full-cycle” for firefox
- middleware/ui: numberlist crawler for DEPATISnet
- middleware/ui: numberlist crawler for FulltextPRO

2015-01-09 0.84.0
=================
- tests: add tests for patent number normalization routines
- tests: adapt tests for patent number normalization routines to enhancements of normalization algorithms for AT- and JP-offices
- middleware: pass through not-normalizable numbers from 3rd-party datasources to OPS
- middleware: number normalization for e.g. BR000PI0507004A
- ui: permit definition of short user-defined keywords (0 chars minimum)

2015-01-09 0.83.2
=================
- middleware: reject bad search syntax in FulltextPRO fulltext field

2015-01-09 0.83.2
=================
- ui: enhance document viewport detection reg. hotkey behaviour; should properly work on last item in list now

2015-01-09 0.83.1
=================
- middleware: finally remove last hack against FulltextPRO deficiencies reg. ipc- vs. cpc-classes

2015-01-08 0.83.0
=================
- middleware: increase DEPATISconnect service run_acquisition request timeout from 3 to 8 seconds;
  hopefully this improves the 502/504 http errors occurring on production
- middleware: switch to modern version of FulltextPRO comfort form -> xml query translation again, allowing nested OR expressions
- middleware/ui: allow "DE,EP" comfort form syntax for countries
- ui: Family citations highlighting: auto generate hsla colors to increase color space
- ui: Family citations highlighting: when saving keyword mappings, remove highlighted keywords before applying highlighting again
- ui: Don't use dismissed basket entries in review mode
- ui: cache "get_numbers" on basket model, this would be called on each "link_document"
- ui: enhance behavior for hitting page bottom when scrolling to next item, simplify code

2015-01-06 0.82.2
=================
- dummy release

2015-01-06 0.82.1
=================
- ui: properly catch condition when there's no family information available

2015-01-06 0.82.0
=================
- ui: add ECMAScript 6 compatibility shim
- ui: explore citation environment of all cited references aggregated across all family members
- ui: highlighting for family citations

2015-01-06 0.81.3
=================
- middleware: cleanup host-based constraints in parameter firewall
- middleware: fix keyword extraction from FulltextPRO fulltext field containing boolean expressions

2015-01-06 0.81.2
=================
- middleware: enhance FulltextPRO IPC/CPC class woes

2015-01-05 0.81.1
=================
- ui: fix keyword decoding for complex queries

2015-01-05 0.81.0
=================
- middleware: bug: “just one IPC class works with FulltextPRO”; another fix for “modern mode => legacy mode”
- middleware/ui: number normalization for numberlists

2015-01-05 0.80.0
=================
- ui: slightly enhance layout of “references cited (56)” data
- ui: scroll to top of window after paging
- ui: pagedown/pageup (space/shift+space) navigation now also utilizes paging when overdrawing
- ui: enhance scrolling- and paging-behaviors

2015-01-05 0.79.0
=================
- ui: fix direct numberlist mode for internet explorer
- middleware: fix FulltextPRO query generation (deactivated "modern mode" due to problems with "FulltextPRO" query parser)
- ui: shortcut button for jumping from bibliographic data directly to the “Family » Citations” tab

2015-01-04 0.78.0
=================
- auth: fix authentication.lua re. “came_from”
- ui: "family citations" prototype

2015-01-04 0.77.1
=================
- ui: minor tweaks to custom highlighting style

2015-01-04 0.77.0
=================
- auth: fix "came_from" functionality

2015-01-04 0.76.0
=================
- ui: enhance custom highlighting style

2015-01-04 0.75.0
=================
- ui: display badges for patentsearch-staging and -develop
- ui: extend copyright line to current year (2015)
- ui: enable all modules in development mode

2015-01-04 0.74.0
=================
- ui: fix - highlighting stopped working when displaying document details (claims, description)
- ui: enhance custom highlighting

2014-12-16 0.73.0
=================
- ui: individual keyword highlighting - prototype

2014-12-15 0.72.0
=================
- middleware: propagate userid upstream to middleware and resolve user detail information from MongoDB
- middleware: use OPS credentials from user details, otherwise fall back to Elmyra OPS credentials
- middleware: publish and enhance OPS usage api
- middleware: per-user, per-day metrics for upstream transfer volume
- middleware: use "modules" info from user details for computing allowed access to FulltextPRO

2014-12-14 0.71.4
=================
- middleware: fix FulltextPRO error messages

2014-12-10 0.71.3
=================
- middleware: fix OPS applicant family analytics

2014-12-10 0.71.2
=================
- middleware: deactivate enhanced flexible class querying at FulltextPRO due to upstream regressions

2014-12-10 0.71.1
=================
- middleware: fix OPS applicant family analytics

2014-12-10 0.71.0
=================
- middleware: OPS applicant family analytics enhancements: word- and image-counts
- middleware: enhance query expression utility service for “applicant” field, e.g. “MAMMUT SPORTS GROUP AG”
- middleware: fix number normalization of AT numbers
- ui: scroll to first result entry after paging
- middleware: enhance/fix drawing inquiry
- ui: display original values of parties (applicant, inventor)
- middleware: make umlauts work at FulltextPRO, e.g. applicant=Kärcher
- middleware: OPS applicant family analytics enhancements: designated states

2014-12-08 0.70.1
=================
- middleware: fix "FulltextPRO" CPC classes import

2014-12-08 0.70.0
=================
- middleware: integrate "FulltextPRO" CPC classes

2014-12-05 0.69.0
=================
- middleware: OPS applicant family analytics prototype

2014-12-04 0.68.0
=================
- middleware: honor "bi=" fieldname in comfort form fulltext search expression
- middleware: minor fix for problems with umlauts in “inventor” field in comfort form
- ui: don’t close document view when switching regions to fix lost event listeners
- ui: link non-patent-literature citations to search.crossref.org

2014-12-02 0.67.0
=================
- middleware: propagate error message from "FulltextPRO" search to user interface
- ui: reset document model on error while avoiding double rendering on initial page load
- middleware/ui: propagate ftpro search exception to user interface
- middleware: fix for boolean fulltext expressions for FulltextPRO search
- ui: enhance/fix error behavior, error display and hotkeys
- ui: enable/fix autocomplete in comfort form (workaround)
- middleware: strip spaces from values of comfort form @ FulltextPRO to fix "FulltextPRO" syntax error
- ui: fix comfort form submit-on-return for non-ie/-safari browsers
- middleware/ui: enhance error message propagation
- middleware/ui: fix/enhance query expression building experience
- middleware: propagate error message about unknown IPC class from FulltextPRO comfort form

2014-12-01 0.66.0
=================
- middleware: allow simple boolean expressions (e.g. ti=bildschirm and ab=fahrzeug) in comfort form for FulltextPRO search

2014-11-24 0.65.1
=================
- fix depatisconnect adapter

2014-11-24 0.65.0
=================
- remove beta badge

2014-11-18 0.64.0
=================
- ui: display other classifications (UC, FI, FTERM)
- middleware: enhance timeout behavior when downloading PDF documents (1 second)
- ui/middleware: fulltext-modifier-chooser for selecting in which fulltext fields
  (title, abstract, claim, description) to search at "FulltextPRO" backend
- ui: fullscreen mode feature

2014-11-17 0.63.0
=================
- ui: display application number

2014-11-16 0.62.3
=================
- ui: remove application date from document header area

2014-11-16 0.62.2
=================
- ui: don't use tables with full borders

2014-11-16 0.62.1
=================
- ui: improve display of inpadoc patent family (compact)

2014-11-16 0.62.0
=================
- ui/middleware: display inpadoc patent family

2014-11-15 0.61.2
=================
- ui: fix database import on Windows

2014-11-14 0.61.1
=================
- ui: fix collectionView / listRegion display woes

2014-11-14 0.61.0
=================
- ui/middleware: new result view showing all search results from FulltextPRO

2014-11-12 0.60.0
=================
- ui/middleware: display nice error message if "FulltextPRO" is in maintenance mode

2014-11-12 0.59.1
=================
- ui: try to make hotkeys work from inside input fields by delaying setup

2014-11-12 0.59.0
=================
- ui: disable google datasource activation shortcut on production

2014-11-12 0.58.0
=================
- middleware: apply number normalization to results from FulltextPRO, enhance number normalization for JP documents

2014-11-11 0.57.0
=================
- ui: renamed “also published as” to “full cycle”
- ftpro backend: use textsearch with fullfamily="false" to satisfy customer requirement
- ftpro backend: apply intermediary hack to allow for simple concatenation with “and” or
  “or” operators of class search expression in comfort form

2014-11-09 0.56.0
=================
- ui: enhance hotkey handling
- ui: update jquery.hotkeys.js
- ui: add feature to query by numberlist

2014-11-08 0.55.1
=================
- ui: enhancements to zoomed form field hotkey handling

2014-11-08 0.55.0
=================
- ui: comfort form input field zooming and hotkey improvements

2014-11-07 0.54.0
=================
- ui: make google datasource invisible by default

2014-11-07 0.53.0
=================
- ui/middleware: lazy acquisition of german abstracts for DE documents from DEPATISconnect

2014-11-06 0.52.0
=================
- ui: enhance and stabilize query behavior, user experience and keyword propagation

2014-11-06 0.51.0
=================
- ui: full-cycle mode chooser
- middleware: allow searching for discrete ipc classes at FulltextPRO

2014-11-06 0.50.1
=================
- ui: fix minor typo

2014-11-06 0.50.0
=================
- ui: fix ftpro keyword propagation
- ui: change text on login form: beta => 14 day trial
- deployment: add target “vdpm”
- ui/middleware: integrated Google Patents
- ui/middleware: lots of refactoring

2014-11-05 0.49.0
=================
- ui/middleware: fix for weird Chrome bug: "X-PatZilla-Query-Keywords" headers are recieved duplicated
- ui: paging layout overflow fix for Internet Explorer

2014-11-05 0.47.0
=================
- ui: fix: only set query and keywords if non-empty after computing query expression

- deployment: whitelist FulltextPRO for domain patentsearch.vdpm.elmyra.de
- misc: enhance error message when OPS is in maintenance mode
- middleware/ui: enhance paging mechanics with propagation to datasource and lazy fetching
- ui: cosmetic fixes
- ui: deactivate Export (Report) functionality

2014-10-08 0.46.0
=================
- middleware/ui: compute keywords from comfort form field values if datasource=ftpro
- middleware/ui: enhance error handling on invalid field values in "FulltextPRO" comfort form
- middleware: enable "FulltextPRO" IPC class querying with right truncation, e.g. H04L29*

2014-10-08 0.45.0
=================
- middleware/ui: connect comfort search form with ftpro datasource
- middleware: "FulltextPRO" concordance subsystem for resolving countries and ipc classes

2014-10-07 0.44.2
=================
- middleware: activate ftpro query caching
- ui: just parse ftpro results if result count >0

2014-10-07 0.44.1
=================
- rename file for an attempt on dependency mungling

2014-10-07 0.44.0
=================
- middleware: lowlevel adapter to search provider "SIP/FulltextPRO"
- ui/middleware: integrate "FulltextPRO" search provider into user interface

2014-10-04 0.43.2
=================
- middleware: when performing patentnumber normalization, strip leading zeros from JP document numbers
  (DEPATISnet yields numbers like JP002011251389A)

2014-09-12 0.43.1
=================
- fix pdf url at new “also published as” bibliographic data

2014-09-12 0.43.0
=================
- data: stay in full-cycle mode, but only use first result document as representative one
- data: enrich representative document with "also published as" bibliographic data
- ui: display “also published as” information

2014-09-05 0.42.0
=================
- api: endpoint for inquiring all publication kindcodes by publication reference

2014-08-07 0.41.0
=================
- fix highlighting for descriptions from DEPATISconnect

2014-08-04 0.40.0
=================
- middleware: api endpoint for downloading a zip archive of multiple pdf documents
- ui: wire multiple pdf zip archive download
- ui: various minor improvements, some javascript refactoring
- ui/middleware: lots of minor tweaks, more icons for notifications, wording
- ui: import and share numberlist from/via clipboard

2014-08-03 0.39.0
=================
- ui: improve field autofocus behavior
- ui: switch to expert mode when receiving url parameter ?query=
- middleware: fix UserHistory.userid uniqueness

2014-08-03 0.38.0
=================
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

2014-08-01 0.37.0
=================
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

2014-08-01 0.36.0
=================
- ui/data: properly deserialize ops response reg. nested results
- ui: compute cql query from comfort form fields already when switching tabs
- ui: query builder action button reorganization
- ui: basket action button reorganization
- ui: project action button reorganization
- ui: swap tabs: Biblio, Claims, Desc
- ui: rename “basket” to “collection”
- ui: more action button enhancements
- ui: put comment button right next to "Biblio, Claims, Desc"

2014-08-01 0.35.0
=================
- middleware: run ops search with "full-cycle" to retrieve A3 and B1 documents and more

2014-07-31 0.34.0
=================
- ui: refactor query builder to separate component
- ui: introduce field-based query builder (comfort flavor)
- ui: update cql field chooser for DEPATISnet
- ui: change font for basket display

2014-07-16 0.33.0
=================
- ui: fix patoffice integration; submit basket content without rating stars
- ui: fix broken inline links; don't propagate "datasource=depatisnet”, but explicitly switch to “datasource=ops” instead
- ui: better demo query for login panel
- auth: use session cookies instead of persistent cookies for propagating the authentication token
- auth: use "Secure" for making cookies https-only
- middleware/auth: timestamps  for User (created, modified)

2014-07-14 0.32.0
=================
- auth/identity/ui: propagate user tags to middleware, implement user create form; only permit for elmyra staff

2014-07-14 0.31.4
=================
- minor fixes and updates

2014-07-14 0.31.3
=================
- middleware: "RNG must be re-initialized after fork()" fixing again

2014-07-14 0.31.2
=================
- middleware: fix nasty "AssertionError: PID check failed. RNG must be re-initialized after fork(). Hint: Try Random.atfork()"
  error with opaque parameter subsystem

2014-07-14 0.31.1
=================
- auth/ui: tweak login form, fix cookie renewal

2014-07-14 0.31.0
=================
- auth/ui: make login screen more appealing
- auth/ui: sign out with button
- ui: permalink to current query
- auth: always permit access to “patentview” domains

2014-07-14 0.30.0
=================
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

2014-07-10 0.29.0
=================
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

2014-07-04 0.28.0
=================
- middleware: fix charset encoding when propagating cql query to DEPATISnet
  and extracting keywords; enhance keyword processing

2014-07-03 0.27.0
=================
- middleware: updated cheshire cql parser from upstream re. “style: PEP8 fixes for core modules”
- middleware: make cheshire cql parser smarter by allowing value shortcut notations
  like 'index=(term)' or 'index=(term1 and term2 or term3)'
- middleware: tests for value shortcut notation extension of cheshire cql parser

2014-06-24 0.26.1
=================
- ui: fix query-links in liveview mode

2014-06-24 0.26.0
=================
- ui: add "keyboarder" library
- ui: add “list-group” css from bootstrap3
- ui: add help page
- ui: add hotkey overview to help page
- ui: fix/improve inline query-link parameter building

2014-06-24 0.25.1
=================
- fix/improve build and deployment infrastructure

2014-06-24 0.25.0
=================
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

2014-06-22 0.24.3
=================
- ui: attempt to fix link expiry display

2014-06-22 0.24.2
=================
- release release

2014-06-22 0.24.1
=================
- ui, middleware: propagate metadata of signed opaque parameter token downstream to show link expiry time (ttl) in user interface

2014-06-22 0.24.0
=================
- ui, parameters: add button to popover for opening permalinks, tune urlcleaner regex
- ui: added “ZeroClipboard 2.1.2”
- ui: add button to copy permalink to clipboard

2014-06-22 0.23.4
=================
- ui, parameters: fix bootstrapping via "numberlist" query parameter

2014-06-22 0.23.3
=================
- ui: minor fix when displaying the current project name without having one
- ui: increased default opaque parameter ttl to 24 hours

2014-06-22 0.23.2
=================
- ui: attempt to fix opaque parameter mechanics for inline “query-link”s

2014-06-22 0.23.1
=================
- ui: attempt to fix permalinks re. baseurl linking

2014-06-22 0.23.0
=================
- middleware: add “translogger” to development.ini to have an access.log
- ui: clean huge url parameters like “database” or “op” from url at an early stage using the HTML5 history API to avoid referrer spam
- ui/javascript infrastructure: adapt Makefile and MANIFEST
- ui, storage: fix localforage.clear on localStorage to only wipe the current database
- middleware: add some request variables (host-, and path-information) to application configuration
- ui: make permalink buttons show popovers with full uris in text input form elements
- ui, storage: resolve “duplicate project name problem” when importing database to "context=viewer"
- ui: improve permalink mechanics
- middleware: deactivate translogger (for access.log)

2014-06-15 0.22.2
=================
- ui: add “lz-string” library
- ui: compress "data" url with "lz-string"

2014-06-15 0.22.1
=================
- ui, middleware: fix viewer lockdown mode for patentview.elmyra.de

2014-06-15 0.22.0
=================
- middleware: attempt to fix url routing re. undesired infinite redirect loops
- middleware: bind host=patentview.elmyra.de to mode=liveview and title=Patent view
- ui: interactively generate opaque permalinks
- ui: use "opaquelinks" subsystem for review-in-liveview-with-ttl permalinks

2014-06-15 0.21.1
=================
- ui, middleware: deployment aftermath fixes (setup.py dependencies, config.js woes)

2014-06-15 0.21.0
=================
- middleware, ui: "opaquelinks" subsystem on top of JSON Web Tokens
- ui: use "opaquelinks" subsystem for generating inline links in liveview mode
- ui, middleware: major parameter fiddling overhaul
- ui: enable fanstatic minified mode

2014-06-13 0.20.1
=================
- ui [fix]: don't rebuild comments everytime list gets focus
- ui, ux: improve post database wipe experience
- ui: fix document color indicator when document is just added to basket, without any score or dismiss flag set
- ui, ux: display activity indicator and permalink buttons in liveview

2014-06-13 0.20.0
=================
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

2014-06-12 0.19.0
=================
- ui: improved application vs. project bootstrapping
- ui: improved quick notification helper
- ui, storage: database import
- ui, storage: improve backup format

2014-06-12 0.18.0
=================
- ux: make the pdf open on shift+p
- ui, storage: update backbone-relational to b8ab71a449ff (2014-06-10)
- ui, storage: presumably fix object corruption woes with localforage.backbone
- ui, storage: comments plugin, alpha, also opens on "c" key
- ui, storage: update to latest localforage 3ef964cda96 for getting an array of all keys for backup feature
- js: add Blob.js and FileSaver.js for saving files locally without user interaction
- ui, storage: database export, database wipe

2014-06-09 0.17.0
=================
- ui: color indicator for score/dismiss state
- ui: improve document header layout
- ux: improve hotkey assignments
    - right, left: navigate the tabs
    - shift+right, shift+left: navigate the drawings carousel
    - p: open the ops pdf
    - shift+e, shift+d: open espacenet re. depatisnet
    - alt+shift+e, alt+shift+d: open epo register re. dpma register
    - shift+c: open ccd viewer

2014-06-09 0.16.1
=================
- ui: fix "review" regression
- ui: rename OPS => EPO, DEPATISnet => DPMA, adapt hotkeys
- ui: improve rating:
    - get rid of "added, but not rated" state
    - get rid of "plus" button, just leave "trash" button for removing an item
- ux: improve hotkey assignments
- ui: improve document header layout
- ui: improve rating widget layout

2014-06-09 0.16.0
=================
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

2014-06-08 0.15.0
=================
- ui: add “notify.js”
- ui: improve basket, add BasketEntryModel
- ui: fix fulltext display, raw content nodes might not be lists
- ui: also record depatisnet queries, improved query recording in general
- ui: don’t use depatisnet as default datasource
- ui: fix highlighting edge case again
- ux: add jquery.viewport
- ux: hotkeys + and - for adding/removing the document in viewport to/from basket
- ux: snapped scrolling with spacebar

2014-06-07 0.14.0
=================
- attempt to fix result list pdf export
- ui: move project chooser above basket
- ui: cql history chooser

2014-06-05 0.13.1
=================
- ui: improve layout of publication date and application date
- ui: fix missing popover after switching inline detail view
- ui: disable button which shows basket entry count

2014-06-04 0.13.0
=================
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

2014-06-03 0.12.0
=================
- limit citatory query to 10 items due to ops restriction
- ui: modify/extend citation link buttons
- ui: "new project" action
- ui: display number of entries in basket
- ui: improve classification display: add ipc and cpc classes
- ui: display priority claims
- ui: display application number

2014-06-02 0.11.0
=================
- ui: propagate project context across inline query links
- ui: share basket via email
- ui: link to citatory documents

2014-05-26 0.10.4
=================
- ui, storage: fix nasty bug with basket.remove operation

2014-05-26 0.10.3
=================
- meta: add OpenSearch description
- ui, storage: improved robustness, honor asynchronous callback flow
- ui, storage: delete project
- ui: reposition and redesign project chooser
- ui: trigger project reload when window gets focus

2014-05-24 0.10.2
=================
- ui, storage: [fix] automatically update the "project.modified" attribute when manipulating the basket

2014-05-24 0.10.1
=================
- ui: make "modified" attribute humanly readable in project chooser widget
- ui, storage: automatically update the "project.modified" attribute when manipulating the basket

2014-05-24 0.10.0
=================
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

2014-05-24 0.9.0
================
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

2014-05-21 0.8.1
================
- link javascript resources

2014-05-20 0.8.0
================
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

2014-05-15 0.7.4
================
- update jquery.hotkeys.js
- ui: remove "beta" badge
- ui: bind search to hyper+return and ctrl+return keys

2014-05-08 0.7.3
================
- DEPATISnet integration: more fixes

2014-05-08 0.7.2
================
- DEPATISnet integration: minor fixes

2014-05-08 0.7.1
================
- ui, middleware: proper DEPATISnet integration
- cache search queries for one hour

2014-05-07 0.7.0
================
- search at DPMA DEPATISnet: prototype
- ui: highlight "bi" search terms in abstract

2014-04-02 0.6.7
================
- fix query parameter backwards compatibility: ship_url vs. ship-url

2014-03-22 0.6.6
================
- fix switch to patentsearch.elmyra.de for /office urls

2014-03-22 0.6.5
================
- ui: drawings-carousel: request image information asynchronously to make result list display snappy again
- fix direct access url semantics in local development (hack)

2014-03-22 0.6.4
================
- fix direct access url semantics

2014-03-22 0.6.3
================
- ui: add "beta" badge to title
- ui: drawings-carousel: always request image information to display fully qualified "Drawing #1/2"
- ui: make widths of all widgets equal
- switch to patentsearch.elmyra.de
- better url semantics for direct access, e.g. /num/EP666666

2014-03-21 0.6.2
================
- refactor application layout on code level
- ui: refactor basket into solid marionette component
- ui: add localForage library
- ui: temporarily remove cql quick query builder helper actions
- ui: make pagination links black, not blue
- ui: fix link to CCD Viewer (upgrade from /CCD-2.0.0 to /CCD-2.0.4)
- ui: print/pdf: honor current query and pagesize

2014-03-21 0.6.1
================
- middleware: fix result pdf rendering by using http url instead of https

2014-03-16 0.6.0
================
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

2014-03-16 0.5.1
================
- dev/prod: try to exclude development javascript sources from source package

2014-02-23 0.5.0
================
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

2014-02-21 0.4.2
================
- dev: fix .bumpversion.cfg

2014-02-21 0.4.1
================
- ui: click on document-number in header to navigate to this document
- ui: enhance pager, display active pagination entry, display current range
- ui: open drill-down links in external window
- ui: move arrow controls of carousel to bottom of image
- ui: center "Drawing #1" label below image
- ui: don't show "Drawing #1" label when there's no image
- ui: drawing carousel: show total number of drawings in status line
- dev: prepare automatic version bumping

2014-02-21 0.4.0
================
- api: add a little cql smartness: wrap cql query string with
       quotes if query contains spaces and is still unquoted
- api: enhance image information, publish via endpoint
- ui: carousel for drawings
- ui: display pager on top of and at bottom of resultlist
- ui: don't show pagers when there are no results yet
- ui: link to family information (INPADOC, OPS)
- ui: display cited references below abstract

2014-02-20 0.3.0
================
- middleware: create full pdf documents from single pages via ops only
- ui: offer full pdf document from multiple sources
- ui/middleware: apply links to applicants, inventors, ipc classes and publication date

2014-02-19 0.2.2
================
- middleware: add DPMAregister smart access subsystem
- api: publish DPMAregister smart access subsystem, e.g.
  /jump/dpma/register?pn=DE19630877
- ui: display link to uspto pair

2014-02-19 0.2.1
================
- ui/api: evaluate and display upstream error responses
- middleware: adjust image level while converting from tiff to png
- ui: remove (54) entry prefix
- ui: refactor header
- middleware: also cache output of tiff-to-png conversion for drawings
- ui: style header buttons inline with others (gray, not turquoise)
- ui: gray background, refactor query area
- ui: link to legal status information from various patent offices
  (European Patent Register, INPADOC legal status, DPMAregister)

2014-02-19 0.2.0
================
- ui: show alternative text when no drawing image is available instead of broken image symbol
- ui: download full pdf document from espacenet instead of having single-page images only
- ui: resize first drawing image to 457px width to avoid resizing in browsers
- ui/feature: "review" selected documents
- api/ui: propagate "numberlist" query parameter value into basket
- api/middleware: document-number normalization on patent-search endpoint for "pn=" attributes
- middleware: resource caching
    - search: 5 minutes
    - static: 1 year

2014-02-16 0.1.1
================
- pdf.svg problems: fix MANIFEST, fix setup.py

2014-02-16 0.1.0
================
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

2014-02-01 0.0.12
=================
- api endpoint for retrieving fullimage documents as pdf
- ui: modal pdf viewer with paging

2014-01-14 0.0.11
=================
- api endpoint for retrieving family publications in xml

2013-11-26 0.0.10
=================
- add ops oauth client
- inline display first drawing

2013-11-25 0.0.9
================
- show result count in pagination area
- application structure refactoring and streamlining
- prepare inline display of first drawing

2013-11-12 0.0.8
================
- ship-mode=single-bibdata: rename "submit" form button name to "ship_action"

2013-10-24 0.0.7
================

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

2013-10-14 0.0.6
================
- fix "abstract" parsing

2013-10-14 0.0.5
================
- fix packaging and deployment issues

2013-10-14 0.0.4
================
- upgrade to 'js.marionette==1.1.0a2'

2013-10-14 0.0.3
================
- moved js.marionette to github
- enhanced deployment code "make install" reg. versioning
- fix "abstract" parsing, e.g. @ WO2013148409A1
- applicant=ibm => cannot use method "join" on undefined
- neu: anmeldedatum
- simple static paging from 1-200, 25 each
- spinner icon for showing activity

2013-10-09 0.0.2
================
- changed production.ini port to 9999
- renamed js.underscore.string to js.underscore_string
- Makefile and fabfile.py for common sysop tasks
- renamed some ingress query parameters to "ship_*"
- cleaned up url parameter propagation

2013-10-09 0.0.1
================
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
