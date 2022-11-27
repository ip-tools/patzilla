# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import json

from click.testing import CliRunner

import pytest

from patzilla.access.generic.exceptions import SearchException
from patzilla.access.ificlaims.clientpool import IfiClaimsCredentialsGetter
from patzilla.commands import cli


try:
    IfiClaimsCredentialsGetter.from_environment()
except KeyError:
    pytestmark = pytest.mark.skip(reason="No IFICLAIMS credentials provided")


def test_command_ificlaims_search_success():
    """
    Proof that `patzilla ificlaims search` works as intended.
    """
    runner = CliRunner()

    result = runner.invoke(cli, "--verbose ificlaims search pn:EP0666666", catch_exceptions=False)
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert data["meta"]["navigator"]["count_total"] == 3
    assert data["meta"]["upstream"]["status"] == "success"
    assert data["meta"]["upstream"]["params"]["q"] == "pn:EP0666666"
    assert data["numbers"] == ["EP0666666B1", "EP0666666A3", "EP0666666A2"]
    assert len(data["details"]) == 3


def test_command_ificlaims_search_failure():
    """
    Proof that bad input to `patzilla ificlaims search` croaks as intended.
    """
    runner = CliRunner()

    with pytest.raises(SearchException) as ex:
        runner.invoke(cli, "ificlaims search foo:bar", catch_exceptions=False)
    ex.match("Response status code: 400")
    ex.match("undefined field foo")
