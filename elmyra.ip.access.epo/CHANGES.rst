============================
elmyra.ip.access.epo CHANGES
============================

development
===========

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
