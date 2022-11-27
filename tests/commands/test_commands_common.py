# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import sys

from configparser import ConfigParser

import pytest

from patzilla.commands import cli


def test_command_make_config(capsys):
    """
    Proof that `patzilla make-config ... --flavor=docker-compose` works as intended.

    It should yield a configuration which contains `mongodb` as host name
    for connecting to MongoDB. That fits the Docker Compose configuration
    provided within the repository.
    """

    # Invoke cli command.
    sys.argv = ["patzilla", "make-config", "production", "--flavor=docker-compose"]
    with pytest.raises(SystemExit) as ex:
        cli()
    assert ex.value.code == 0

    # Read configuration file content from STDOUT.
    config_payload = capsys.readouterr().out

    # Parse and verify configuration details.
    config = ConfigParser()
    config.read_string(string=config_payload, source="{}.ini".format("production"))
    assert config.get("app:main", "mongodb.patzilla.uri") == "mongodb://mongodb:27017/patzilla"
