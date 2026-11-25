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
    Configure and bootstrap the application environment at runtime, without
    running an HTTP server. This is used by command line programs and software tests.

    When no configuration file is given, the `PATZILLA_CONFIG` environment variable
    is checked, and otherwise a configuration file is created on demand using the
    `BootConfiguration`.

    Returns a dictionary with the keys `app`, `registry`, `request`, and `closer`.
    """
    from patzilla.web.app import bootstrap

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

    # Bootstrap application.
    env = bootstrap(configfile_application)

    # When booting a minimal application, dispatch the request events once,
    # in order to attach data source client objects to the request object.
    if bootconfiguration and bootconfiguration.flavor == "minimal":
        dispatch_request_events(env)

    return env


def dispatch_request_events(env):
    """
    Run request subscribers, for example to attach data source client pool objects to the request object.
    """
    request = env['request']
    registry = env['registry']
    registry.notify_request(request)
