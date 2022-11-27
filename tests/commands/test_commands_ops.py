# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import json

from click.testing import CliRunner

import pytest
from pyramid.httpexceptions import HTTPNotFound

from patzilla.access.epo.ops.client import OpsCredentialsGetter
from patzilla.commands import cli


try:
    OpsCredentialsGetter.from_environment()
except KeyError:
    pytestmark = pytest.mark.skip(reason="No OPS credentials provided")


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
