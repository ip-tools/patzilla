# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import json
import sys

from click.testing import CliRunner
from configparser import ConfigParser

import pytest
from pyramid.httpexceptions import HTTPNotFound

from patzilla.access.generic.exceptions import SearchException
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


def test_command_ops_search_success():
    """
    Proof that `patzilla ops search` works as intended.
    """
    runner = CliRunner()

    result = runner.invoke(cli, "--verbose ops search pn=EP0666666B1", catch_exceptions=False)
    assert result.exit_code == 0

    stdout = result.stdout
    assert "<ops:world-patent-data" in stdout
    assert '<ops:biblio-search total-result-count="1">' in stdout


def test_command_ops_search_failure():
    """
    Proof that bad input to `patzilla ops search` croaks as intended.
    """
    runner = CliRunner()

    with pytest.raises(IOError) as ex:
        runner.invoke(cli, "ops search foo=bar", catch_exceptions=False)
    ex.match("An error happened while requesting data from EPO/OPS. Status code was: 400")
    ex.match("CLIENT.InvalidIndex")


def test_command_ops_image_info_success():
    """
    Proof that `patzilla ops image-info` works as intended.
    """
    runner = CliRunner()

    result = runner.invoke(cli, "ops image-info --document=EP0666666B1", catch_exceptions=False)
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert sorted(data.keys()) == ["Drawing", "FirstPageClipping", "FullDocument", "META"]


def test_command_ops_image_info_failure():
    """
    Proof that `patzilla ops image-info` works as intended.
    """
    runner = CliRunner()

    with pytest.raises(HTTPNotFound) as ex:
        runner.invoke(cli, "ops image-info --document=EP123A2", catch_exceptions=False)
    ex.match("No image information for document=EP123A2")


def test_command_ops_image_fulldocument_pdf_success():
    """
    Proof that `patzilla ops image` works as intended. Request document as PDF.
    """
    runner = CliRunner()

    result = runner.invoke(cli, "ops image --document=EP0666666B1 --page=1", catch_exceptions=False)
    assert result.exit_code == 0

    assert result.stdout.startswith("%PDF-1.4")
    assert 30000 < len(result.stdout) < 50000


def test_command_ops_image_fulldocument_tiff_success():
    """
    Proof that `patzilla ops image` works as intended. Request document as TIFF.
    """
    runner = CliRunner()

    result = runner.invoke(cli, "ops image --document=EP0666666B1 --page=1 --format=tiff", catch_exceptions=False)
    assert result.exit_code == 0

    assert result.stdout.startswith(b"\x4d\x4d\x00\x2a")


def test_command_ops_image_drawing_pdf_success():
    """
    Proof that `patzilla ops image` works as intended. Request drawing as PDF.
    """
    runner = CliRunner()

    result = runner.invoke(cli, "ops image --document=EP0666666B1 --kind=FullDocumentDrawing --page=1", catch_exceptions=False)
    assert result.exit_code == 0

    assert result.stdout.startswith("%PDF-1.4")
    assert 10000 < len(result.stdout) < 20000


def test_command_ops_image_failure():
    """
    Proof that a bad input to `patzilla ops image` croaks as intended.
    """
    runner = CliRunner()

    with pytest.raises(HTTPNotFound) as ex:
        runner.invoke(cli, "ops image --document=EP123A2 --page=1", catch_exceptions=False)
    ex.match("No image information for document=EP123A2")


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
