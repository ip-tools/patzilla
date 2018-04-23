# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl <andreas.motl@ip-tools.org>
import os
import sys
import csv
import logging
from docopt import docopt
from pprint import pformat, pprint
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
      {program} info
      {program} --version
      {program} (-h | --help)

    Configuration file options:
      make-config               Will dump configuration file content to STDOUT,
                                suitable for redirecting into a configuration file
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
      {program} import <csv-file>

      {program} --version
      {program} (-h | --help)

    User add options:
      --fullname=<fullname>             Full user name, e.g. "Max M. Mustermann"
      --username=<username>             Username / Email address, e.g. test@example.org
      --password=<password>             Password
      --tags=<tags>                     Tags to apply to this user. e.g. "trial"
      --modules=<modules>               Modules to enable for this user. e.g. "keywords-user, family-citations"
      --organization=<organization>     Organization name
      --homepage=<homepage>             Homepage URL
      --phone=<phone>                   Phone number

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
    configfile = os.environ['PATZILLA_CONFIG']

    # TODO: Currently, this is a full bootstrap. It can be trimmed down to database setup only.
    env = setup_commandline_pyramid(configfile)
    #logger = logging.getLogger(__name__)

    # Clean option names
    options = normalize_docopt_options(options)

    # Debugging
    #print('Options:\n{}'.format(pformat(options)))

    if options['add']:
        user = create_user(options)
        if not user:
            sys.exit(1)

    elif options['import']:

        csvfile_path = options['csv-file']
        field_blacklist = ['phone']

        with open(csvfile_path) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:

                # Remove blacklisted fields
                for blackfield in field_blacklist:
                    if blackfield in row:
                        del row[blackfield]

                create_user(row)


def create_user(data):

    # Decode values with comma-separated lists
    for name in ['tags', 'modules']:
        data[name] = read_list(data[name])

    # Create user object
    user = UserManager.add_user(**data)
    if user:
        msg = 'Successfully created user "{}".\n{}'.format(data['username'], user.to_json(indent=4))
        logger.info(msg)

    return user
