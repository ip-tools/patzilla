# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
from __future__ import absolute_import
import logging
import logging.config
import os
import sys

from pyramid.events import ContextFound
from pyramid.paster import bootstrap

from patzilla.boot.config import BootConfiguration

logger = logging.getLogger(__name__)


def setup_pyramid(configfile=None, bootconfiguration=None):
    """
    Configure and bootstrap the Pyramid framework environment.

    Q: Can this be switched completely to runtime-based configuration?
    A: No, `pyramid.paster.bootstrap` apparently will always need a configuration file.

    - https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/commandline.html#writing-a-script
    - https://stackoverflow.com/questions/6206556/running-scripts-within-pyramid-framework-ie-without-a-server
    - https://stackoverflow.com/questions/12510133/share-pyramid-configuration-with-a-cli-script
    """

    # When no configuration file is given, check environment variable first.
    if configfile is None:
        configfile = os.environ.get('PATZILLA_CONFIG')

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
    logging.config.fileConfig(configfile_logging)
    logger.setLevel(logging.DEBUG)
    logger.info("Logging configuration file:    {}".format(configfile_logging))

    # Bootstrap Pyramid.
    env = bootstrap(configfile_application)

    # Get request and registry objects from environment.
    request = env['request']
    registry = env['registry']

    # Run event subscriptions to attach data source client pool objects to request object.
    event = ContextFound(request)
    registry.notify(event)

    return env
