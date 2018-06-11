# -*- coding: utf-8 -*-
# (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
import os
from docopt import docopt

from patzilla.access.sip.concordance import import_countries, import_ipc_classes, import_cpc_classes
from patzilla.util.config import normalize_docopt_options
from patzilla.util.web.pyramid.commandline import setup_commandline_pyramid
from patzilla.version import __version__
from patzilla.util.logging import boot_logging

APP_NAME = 'patzilla-sip'

def run():
    """
    Usage:
      {program} import --kind=<kind> <file> [--force]
      {program} --version
      {program} (-h | --help)

    Options:
      <kind>        One of country, ipc, cpc
      <file>        Path to import file

    Miscellaneous options:
      --debug                   Enable debug messages
      --version                 Show version information
      -h --help                 Show this screen

    Examples:

      # Import country to id map
      patzilla-sip import --kind=country /tmp/ccids.xlsx

      # Import IPC class to id map
      patzilla-sip import --kind=ipc /tmp/ipcids.xlsx

      # Import CPC class to id map
      patzilla-sip import --kind=cpc /tmp/IPC_CPC.csv

    """

    # Use generic commandline options schema and amend with current program name
    commandline_schema = run.__doc__.format(program=APP_NAME)

    # Read commandline options
    options = docopt(commandline_schema, version=APP_NAME + ' ' + __version__)

    # Start logging subsystem
    boot_logging(options)

    # Boot Pyramid to access the database
    configfile = os.environ['PATZILLA_CONFIG']

    # TODO: Currently, this is a full bootstrap. It can be trimmed down to database setup only.
    env = setup_commandline_pyramid(configfile)

    # Clean option names
    options = normalize_docopt_options(options)

    # Debugging
    #print('options: {}'.format(options))

    if options['import']:
        kind = options['kind']
        filepath = options['file']
        force = options['force']
        if kind == 'country':
            import_countries(filepath, force=force)
        elif kind == 'ipc':
            import_ipc_classes(filepath, force=force)
        elif kind == 'cpc':
            import_cpc_classes(filepath, force=force)
