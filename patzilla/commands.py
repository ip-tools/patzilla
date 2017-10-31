# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl <andreas@ip-tools.org>
import logging
from docopt import docopt
from patzilla.util.logging import boot_logging
from patzilla.version import __version__

logger = logging.getLogger(__name__)

APP_NAME = 'patzilla'

def run():
    """
    Usage:
      {program} info
      {program} --version
      {program} (-h | --help)

    Configuration file options:
      <config-kind>             development or production

    Miscellaneous options:
      --debug                   Enable debug messages
      --version                 Show version information
      -h --help                 Show this screen


    """

    # Use generic commandline options schema and amend with current program name
    commandline_schema = run.__doc__.format(program=APP_NAME)

    # Read commandline options
    options = docopt(commandline_schema, version=APP_NAME + ' ' + __version__)

    # Start logging subsystem
    boot_logging(options)

    # Debugging
    #print('options: {}'.format(options))

