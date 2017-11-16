# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl <andreas@ip-tools.org>
import os
import logging
from pprint import pformat, pprint
from docopt import docopt
from patzilla.config import get_configuration
from patzilla.util.config import read_list, normalize_docopt_options
from patzilla.util.logging import boot_logging
from patzilla.util.web.identity.store import UserManager
from patzilla.util.web.pyramid.commandline import setup_commandline_pyramid
from patzilla.version import __version__

logger = logging.getLogger(__name__)

APP_NAME = 'patzilla'

def run():
    """
    Usage:
      {program} make-config <config-kind>
      {program} user add [options]
      {program} info
      {program} --version
      {program} (-h | --help)

    Configuration file options:
      make-config               Will dump configuration file content to STDOUT,
                                suitable for piping into a configuration file
      <config-kind>             One of "development" or "production"

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

    if options['make-config']:
        kind = options['<config-kind>']
        payload = get_configuration(kind)
        print(payload)


def usercmd():
    """
    Usage:
      {program} add [options]

      {program} --version
      {program} (-h | --help)

    User add options:
      --fullname=<fullname>     Full user name, e.g. "Max M. Mustermann"
      --username=<username>     Username / Email address, e.g. test@example.org
      --password=<password>     Password
      --tags=<tags>             Tags to apply to this user. e.g. "trial"
      --modules=<modules>       Modules to enable for this user. e.g. "keywords-user, family-citations"
      --company=<company>       Company name
      --homepage=<homepage>     Homepage URL
      --phone=<phone>           Phone number

    Miscellaneous options:
      --debug                   Enable debug messages
      --version                 Show version information
      -h --help                 Show this screen

    Examples:

      # Configure path to application configuration
      export PATZILLA_CONFIG=/path/to/patzilla.ini

      # Simple add
      patzilla-user add --fullname "John Doe" --username "john.doe@example.org" --password "john123"

      # Add user, enabling some modules
      patzilla-user add \
        --fullname "Max Mustermann" --username "max@example.org" --password "max987" \
        --tags "demo" --modules "keywords-user, family-citations"

    """

    # Use generic commandline options schema and amend with current program name
    commandline_schema = usercmd.__doc__.format(program='patzilla-user')

    # Read commandline options
    options = docopt(commandline_schema, version=APP_NAME + ' ' + __version__)

    # Start logging subsystem
    boot_logging(options)

    # Boot Pyramid to access the database
    # TODO: Currently, this is a full bootstrap. It can be trimmed down to database setup only.
    configfile = os.environ['PATZILLA_CONFIG']
    env = setup_commandline_pyramid(configfile)
    #logger = logging.getLogger(__name__)

    # Debugging
    #print('options: {}'.format(options))

    options = normalize_docopt_options(options)

    if options['add']:

        # Read options with comma-separated lists
        for name in ['tags', 'modules']:
            options[name] = read_list(options[name])

        user = UserManager.add_user(**options)
        if user:
            msg = 'Successfully created user "{}".\n{}'.format(options['username'], user.to_json(indent=4))
            logger.info(msg)

    # Debugging
    #print('options:\n{}'.format(pformat(options)))
