# ================================================
# PatZilla application configuration (development)
# ================================================

[main]
include     = vendors.ini


[ip_navigator]

# Which vendors are enabled?
# The selection process will use the first configured vendor as default, after that it
# will search through the other configured vendors and will select the one which matches
# the "hostname_matches" pattern on a first come, first serve basis.
vendors     = patzilla

# Which datasources are configured?
# Choose one or more of ops, depatisnet, depatisconnect, ificlaims, depatech, sip.
datasources = ops, depatisnet

# Fields to protect from being leaked into Javascript environment
datasources_protected_fields = api_consumer_key, api_consumer_secret, api_uri, api_username, api_password

# Whether to run the instance in development mode
development_mode    = true


# ====================
# Vendor configuration
# ====================

[vendor:patzilla]
organization        = PatZilla
productname         = PatZilla IP Navigator
productname_html    = <span class="header-logo">PatZilla <i class="circle-icon">IP</i> Navigator</span>
page_title          = Patent search
copyright_html      = &copy; 2013-2022, <a href="https://docs.ip-tools.org/patzilla/" class="incognito pointer" target="_blank">The PatZilla Developers</a> — All rights reserved.
stylesheet_uri      = /static/patzilla.css


# ========================
# Datasource configuration
# ========================

[datasource:ops]

# Application-wide authentication credentials
api_consumer_key    = {ops_api_consumer_key}
api_consumer_secret = {ops_api_consumer_secret}

# Q: What is the coverage for full-text descriptions and claims in OPS?
# A: OPS currently supplies descriptions and claims for documents published by the following authorities:
#    EP, WO, AT, BE, BG, CA, CH, CY, CZ, DK, EE, ES, FR, GB, GR, HR, IE, IT, LT, LU, MC, MD, ME, NO, PL, PT, RO, RS, SE, SK
#    - https://www.epo.org/searching-for-patents/data/web-services/ops/faq.html#faq-74
#    - https://www.epo.org/searching-for-patents/technical/full-text-additions.html
#    - https://forums.epo.org/ops-extends-data-coverage-for-character-coded-full-text-xml-to-19-country-collections-7833
fulltext_enabled = true
fulltext_countries = EP, WO, AT, BE, BG, CA, CH, CY, CZ, DK, EE, ES, FR, GB, GR, HR, IE, IT, LT, LU, MC, MD, ME, NO, PL, PT, RO, RS, SE, SK


[datasource:depatisconnect]

# Local development
#api_uri = http://localhost:20300

# Production
api_uri = {depatisconnect_api_uri}

# 2014-07-02: Add fulltexts for DE and US through DEPATISconnect
fulltext_enabled = true
fulltext_countries = DE, US


[datasource:ificlaims]

# API connection settings
api_uri      = {ificlaims_api_uri}
api_uri_json = {ificlaims_api_uri_json}
api_username = {ificlaims_api_username}
api_password = {ificlaims_api_password}

# 2017-03-09: Add fulltexts for more countries through IFI CLAIMS
fulltext_enabled = true
fulltext_countries = BE, CA, CN, FR, GB, IN, JP, KR, LU, NL, RU
# Not enabled yet: EA, SI, ES, IN, AU, HK, BR, PL, CZ, IT, NZ, HU, TR, DK, HR, YU, RS, PT, UA, ZA, SE, MX, NO, BG, SK, TW, AR, GR, ID, IL, FI, DD, CS, MC

details_enabled = true
details_countries = CN, IN, KR


[datasource:depatech]

# API connection settings
api_uri      = {depatech_api_uri}
api_username = {depatech_api_username}
api_password = {depatech_api_password}



# ========================
# Email/SMTP configuration
# ========================

[smtp]
# smtp host information
hostname = {smtp_hostname}
port     = 587              ; smtp submission port, default: 25
tls      = true             ; use TLS, default: true
username = {smtp_username}
password = {smtp_password}

[email_addressbook]

# Sender addresses "From" and "Reply-To"
from        = PatZilla IP Navigator <navigator-system@example.org>
reply       = PatZilla IP Navigator Support <navigator-support@example.org>

# Recipient addresses "To:"
support     = PatZilla IP Navigator Support <navigator-support@example.org>
system      = PatZilla IP Navigator System <navigator-system@example.org>
purchase    = PatZilla IP Navigator Sales <navigator-sales@example.org>


[email_content]

# Email content defaults
subject_prefix = [PatZilla]
body =
    Sehr geehrter Kunde,
    \n
    vielen Dank für Ihre Nachricht!
    \n
    Diese E-Mail wurde aufgrund Ihrer Mitteilung automatisch von unserem Trackingsystem generiert,
    wir werden Ihre Anfrage so schnell wie möglich beantworten.
    \n
    Bitte kommen Sie sonst telefonisch auf uns zu, unsere Telefonnummer finden Sie in der E-Mail Signatur.
    \n
    Mit freundlichen Grüßen,
    Ihr PatZilla IP Navigator Support Team.
    \n
    ----
    \n
    Message:
    {{ message }}
    \n

    {% if details: %}
    Details: {{ details }}
    \n
    {% endif %}

    {% if filenames: %}
    Im Anhang finden Sie weitere technische Details zu Ihrer Anfrage aus dem Systemkontext:
    {{ filenames }}
    \n
    {% endif %}

signature =
    ACME Inc.
    Way 42
    12345 Universe

    Email: info@example.org
    Web: https://example.org



###
# Pyramid application configuration
# http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/environment.html
###

[filter:prefix-middleware]
use = egg:PasteDeploy#prefix

[app:main]
use = egg:patzilla#web
filter-with = prefix-middleware
#filter-with = translogger

pyramid.reload_templates = true
pyramid.debug_authorization = false
pyramid.debug_notfound = false
pyramid.debug_routematch = false
pyramid.default_locale_name = en
#pyramid.includes =
#    pyramid_debugtoolbar

# By default, the toolbar only appears for clients from IP addresses
# '127.0.0.1' and '::1'.
# debugtoolbar.hosts = 127.0.0.1 ::1


# Database configuration
mongodb.patzilla.uri = mongodb://localhost:27017/patzilla_development


# Cache settings
cache.url = mongodb://localhost:27017/beaker.cache
cache.regions = search, medium, longer, static
cache.key_length = 512

cache.search.type = ext:mongodb
cache.search.sparse_collection = true

cache.medium.type = mongodb_gridfs
cache.medium.sparse_collection = true
cache.longer.type = mongodb_gridfs
cache.longer.sparse_collection = true
cache.static.type = mongodb_gridfs
cache.static.sparse_collection = true

# 5 minutes
#cache.search.expire = 300
# 1 hour
#cache.search.expire = 3600
# 2 hours
#cache.search.expire = 7200
# 6 hours
cache.search.expire = 21600
# 1 day
#cache.search.expire = 86400

# medium: 1 day
cache.medium.expire = 86400

# longer: 1 week
cache.longer.expire = 604800

# static: 1 month
cache.static.expire = 2592000



###
# wsgi server configuration
###

[server:main]
use = egg:waitress#main
host = 0.0.0.0
port = 6543

###
# logging configuration
# http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/logging.html
###

[loggers]
keys = root, oauthlib, sqlalchemy, patzilla

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[logger_patzilla]
level = INFO
handlers =
qualname = patzilla

[logger_oauthlib]
level = INFO
handlers =
qualname = oauthlib

[logger_sqlalchemy]
level = INFO
handlers =
qualname = sqlalchemy.engine
# "level = INFO" logs SQL queries.
# "level = DEBUG" logs SQL queries and results.
# "level = WARN" logs neither.  (Recommended for production systems.)


[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-8.8s [%(name)-40s][%(threadName)s] %(message)s


# ---------------------------
#   Paste translogger
#   for having an accesslog
# ---------------------------
# http://pyramid.readthedocs.org/en/latest/narr/logging.html#request-logging-with-paste-s-translogger
[filter:translogger]
use = egg:Paste#translogger
setup_console_handler = False

[logger_wsgi]
level = INFO
handlers = accesslog
qualname = wsgi
propagate = 0

#[handler_accesslog]
#class = FileHandler
#args = ('/var/log/patzilla/access.log','a')
#level = INFO
#formatter = accesslog

[formatter_accesslog]
format = %(message)s
