# -*- coding: utf-8 -*-
# (c) 2017-2022 Andreas Motl <andreas.motl@ip-tools.org>
import os
import sys
import csv
import logging

import click
from docopt import docopt
from patzilla.config import get_configuration
from patzilla.util.config import read_list, normalize_docopt_options
from patzilla.boot.logging import boot_logging
from patzilla.util.web.identity.store import UserManager
from patzilla.boot.framework import setup_pyramid
from patzilla.version import __version__

logger = logging.getLogger(__name__)

APP_NAME = 'patzilla'


@click.group()
@click.version_option()
@click.option("--verbose", is_flag=True, required=False, help="Increase log verbosity.")
@click.option("--debug", is_flag=True, required=False, help="Enable debug messages.")
@click.pass_context
def cli(ctx, verbose, debug):
    # Start logging subsystem.
    boot_logging(dict(debug=debug))


@click.command()
@click.argument("kind", type=str, required=True)
@click.option("--flavor", type=str, required=False,
              help="Use `--flavor=docker-compose` for generating a configuration file suitable "
                   "for use within the provided Docker Compose environment.")
@click.pass_context
def make_config(ctx, kind, flavor):
    """
    Dump blueprint for a configuration file to STDOUT,
    suitable for redirecting into a configuration file.

    The KIND argument takes one of `development` or `production`.

    Examples::

        \b
        # Dump configuration blueprint into target file.
        patzilla make-config production > /path/to/patzilla.ini

        \b
        # Dump configuration blueprint suitable for Docker Compose setup.
        patzilla make-config production --flavor=docker-compose
    """
    payload = get_configuration(kind)

    if flavor:
        # When flavor=docker-compose is requested, adjust the
        # `mongodb.patzilla.uri` and `cache.url` settings.
        if flavor == "docker-compose":
            payload = payload.replace("mongodb://localhost", "mongodb://mongodb")
        else:
            raise ValueError("Unknown configuration file flavor {}".format(flavor))

    print(payload)


cli.add_command(cmd=make_config, name="make-config")


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
    env = setup_pyramid(configfile)
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
