import csv
import json
from io import BytesIO, StringIO
from types import SimpleNamespace
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from munch import munchify
from openpyxl import load_workbook
from patzilla.web.exceptions import HTTPNotFound

from patzilla.navigator import export
from patzilla.navigator.export import Dossier, DossierXlsx


@pytest.fixture
def dossier_data():
    return {
        "project": {
            "name": "Test project",
            "created": "2024-01-01T12:00:00Z",
            "modified": "2024-01-02T12:00:00Z",
            "queries": [{}],
        },
        "user": {"fullname": "Test User", "username": "test@example.org"},
        "queries": [{
            "query_data": {"criteria": {"title": "battery"}},
            "query_expression": "battery",
            "result_count": "12",
            "datasource": "OPS",
            "created": "2024-01-01",
        }],
        "collections": {
            "rated": [{"number": "EP0007054A1", "score": 2}],
            "dismissed": [],
            "seen": [],
        },
        "comments": [{
            "parent": "EP0007054A1",
            "text": "Relevant document",
            "modified": "2024-01-02",
        }],
    }


def test_metadata_and_csv(dossier_data):
    dossier = Dossier(dossier_data)

    assert dossier.metadata["queries_count"] == 1
    assert dossier.metadata["total_search_count"] == 12
    assert dossier.metadata["total_review_count"] == 1
    assert dossier.metadata["datasource_list"] == "OPS"
    assert "Test project" in dossier.get_summary()

    csv_text = dossier.to_csv(dossier.df_documents).decode("utf-8")
    rows = list(csv.DictReader(StringIO(csv_text)))
    assert rows[0]["document"] == "EP0007054A1"


def test_zip_contains_selected_reports(dossier_data):
    dossier = Dossier(dossier_data)
    options = munchify({
        "report": {"xlsx": False, "pdf": False, "csv": True, "json": True},
        "media": {
            "pdf": False, "biblio": False, "description": False,
            "claims": False, "register": False, "family": False,
        },
    })

    with ZipFile(BytesIO(dossier.to_zip(options=options))) as archive:
        names = set(archive.namelist())
        assert {
            "@metadata.txt",
            "@summary.txt",
            "report/csv/01-queries.csv",
            "report/csv/02-documents.csv",
            "report/csv/03-comments.csv",
            "report/json/01-queries.json",
            "report/json/02-documents.json",
            "report/json/03-comments.json",
        } <= names
        assert "report/@dossier.xlsx" not in names

        queries = json.loads(archive.read("report/json/01-queries.json"))
        assert queries[0]["hits"] == 12
        assert json.loads(queries[0]["criteria"]) == {"title": "battery"}

        documents = json.loads(archive.read("report/json/02-documents.json"))
        assert documents[0]["document"] == "EP0007054A1"


def test_xlsx_contains_queries_and_comments(dossier_data, tmp_path, monkeypatch):
    # DossierXlsx initially opens a file named temp.xlsx.
    monkeypatch.chdir(tmp_path)
    payload = DossierXlsx(dossier_data).create()

    workbook = load_workbook(BytesIO(payload), data_only=True)
    try:
        assert set(workbook.sheetnames) == {
            "cover", "queries", "rated", "dismissed", "seen", "comments",
        }
        assert workbook["queries"]["B2"].value == "battery"
        assert workbook["comments"]["B2"].value == "Relevant document"
    finally:
        workbook.close()


def test_zip_reports_delivered_and_missing_media(dossier_data, monkeypatch):
    biblio = Mock(return_value=b"<biblio/>")
    register = Mock(side_effect=HTTPNotFound())
    monkeypatch.setattr(export, "get_ops_biblio_data", biblio)
    monkeypatch.setattr(export, "ops_register", register)

    options = munchify({
        "report": {"xlsx": False, "pdf": False, "csv": False, "json": False},
        "media": {
            "pdf": False, "biblio": True, "description": False,
            "claims": False, "register": True, "family": False,
        },
    })
    request = SimpleNamespace(errors=["stale error"])

    payload = Dossier(dossier_data).to_zip(request=request, options=options)

    with ZipFile(BytesIO(payload)) as archive:
        assert archive.read("media/xml/EP0007054A1.biblio.xml") == b"<biblio/>"
        assert "media/xml/EP0007054A1.register.xml" not in archive.namelist()
        report = archive.read("media/xml/@report.txt").decode("utf-8")
        assert "Delivered artifacts (1):" in report
        assert "Missing artifacts (1):" in report
        assert "biblio" in report
        assert "register" in report

    assert request.errors == []
    biblio.assert_called_once_with("publication", "EP0007054A1", xml=True)
    register.assert_called_once_with("publication", "EP0007054A1", xml=True)


@pytest.mark.parametrize("conversion_fails", [False, True])
def test_zip_handles_pdf_conversion(dossier_data, monkeypatch, conversion_fails):
    class StubXlsx:
        def __init__(self, data):
            pass

        def create(self):
            return b"workbook"

        def to_pdf(self, payload=None):
            assert payload == b"workbook"
            if conversion_fails:
                raise RuntimeError("conversion failed")
            return b"pdf"

    monkeypatch.setattr(export, "DossierXlsx", StubXlsx)
    options = munchify({
        "report": {"xlsx": True, "pdf": True, "csv": False, "json": False},
        "media": {
            "pdf": False, "biblio": False, "description": False,
            "claims": False, "register": False, "family": False,
        },
    })

    payload = Dossier(dossier_data).to_zip(options=options)

    with ZipFile(BytesIO(payload)) as archive:
        assert archive.read("report/@dossier.xlsx") == b"workbook"
        if conversion_fails:
            assert "report/@dossier.pdf" not in archive.namelist()
        else:
            assert archive.read("report/@dossier.pdf") == b"pdf"
