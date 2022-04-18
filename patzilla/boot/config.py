# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
import tempfile
from copy import copy


class BootConfiguration:
    """
    Provide configuration file snippets to the Pyramid environment bootloader.
    It is needed when configuring the application at runtime.
    """

    # A minimal snippet for configuring PatZilla.
    INI_APPLICATION = """
# PatZilla application configuration
#
# For a full variant, see:
# https://github.com/ip-tools/patzilla/blob/main/patzilla/config/development.ini.tpl

[app:main]
use = egg:patzilla#minimal

[ip_navigator]
datasources = {datasources}
    """.strip()

    # The full snippet for configuring the logging subsystem.
    INI_LOGGING = """
# Logging configuration
# See also: http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/logging.html

[loggers]
keys = root, oauthlib, sqlalchemy, patzilla

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

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

[logger_patzilla]
level = INFO
handlers =
qualname = patzilla


[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-8.8s [%(name)-40s] %(message)s
    """.strip()

    def __init__(self, datasources=None):
        self.datasources = datasources or []
        self._tmpfiles = []

    @property
    def for_logger(self):
        return self.tmpfile(self.INI_LOGGING, suffix=".ini")

    @property
    def for_application(self):
        application_ini = copy(self.INI_APPLICATION)
        application_ini = application_ini.format(datasources=", ".join(self.datasources))
        return self.tmpfile(application_ini, suffix=".ini")

    def tmpfile(self, payload, suffix=None):
        """
        Create a temporary file with given content.
        """
        tmp = tempfile.NamedTemporaryFile(suffix=suffix)
        self._tmpfiles.append(tmp)
        tmp.write(payload)
        tmp.flush()
        tmp.seek(0)
        return tmp.name
