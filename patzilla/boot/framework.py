# -*- coding: utf-8 -*-
# (c) 2014-2026 Andreas Motl <andreas.motl@ip-tools.org>
from __future__ import absolute_import
import logging
import logging.config
import os
import sys

from patzilla.boot.config import BootConfiguration

logger = logging.getLogger(__name__)


def setup_environment(configfile=None, bootconfiguration=None):
    """
    Configure and bootstrap the application environment at runtime, without an HTTP server.
    Used by command line programs and software tests. Returns `{"settings": ..., "state": ...}`.

    When no configuration file is given, the `PATZILLA_CONFIG` environment variable is checked,
    otherwise a configuration file is created on demand using the `BootConfiguration`.
    """
    from patzilla.web.settings import WebSettings
    from patzilla.web.state import build_state

    # When no configuration file is given, check environment variable first.
    if configfile is None:
        configfile = os.environ.get('PATZILLA_CONFIG')

    if configfile is not None:
        sys.stderr.write('Loading configuration file: {}\n'.format(configfile))

    # Use given configuration file or create on demand.
    configfile_logging = configfile
    configfile_application = configfile
    if configfile is None:
        if bootconfiguration is None:
            bootconfiguration = BootConfiguration()
        configfile_logging = bootconfiguration.for_logger
        configfile_application = bootconfiguration.for_application

    # Setup logging.
    if configfile_logging:
        if "PYTEST_CURRENT_TEST" not in os.environ:
            logging.config.fileConfig(configfile_logging, disable_existing_loggers=False)
    logger.setLevel(logging.DEBUG)
    logger.info("Logging configuration file:    {}".format(configfile_logging))

    settings = WebSettings.from_ini(configfile_application)
    return {"settings": settings, "state": build_state(settings)}
