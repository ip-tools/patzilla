import csv
import json
from io import BytesIO, StringIO
from types import SimpleNamespace
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from munch import munchify
from openpyxl import load_workbook
from pyramid.httpexceptions import HTTPNotFound

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


def test_odt_contains_document_details(dossier_data, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from xml.etree import ElementTree

    from pyramid.httpexceptions import HTTPNotFound
    from patzilla.navigator import export

    biblio = b"""\
<exchange-documents xmlns="http://www.epo.org/exchange">
  <exchange-document>
    <bibliographic-data>
      <invention-title lang="en">A test invention</invention-title>
    </bibliographic-data>
    <abstract lang="en"><p>Test abstract</p></abstract>
  </exchange-document>
</exchange-documents>
"""
    get_biblio = Mock(return_value=biblio)
    get_family = Mock(return_value=SimpleNamespace(items=[]))
    get_image = Mock(side_effect=HTTPNotFound())

    monkeypatch.setattr(export, "get_ops_biblio_data", get_biblio)
    monkeypatch.setattr(export, "ops_family_members", get_family)
    monkeypatch.setattr(export, "get_ops_image", get_image)

    payload = export.DossierText(dossier_data).create()

    with ZipFile(BytesIO(payload)) as archive:
        assert archive.read("mimetype") == b"application/vnd.oasis.opendocument.text"
        content = ElementTree.fromstring(archive.read("content.xml"))
        text = " ".join(content.itertext())
        assert "Test project" in text
        assert "EP0007054A1" in text
        assert "A test invention" in text
        assert "Relevant document" in text
        assert "Test abstract" in text

    get_biblio.assert_called_once_with("publication", "EP0007054A1", xml=True)
    get_family.assert_called_once_with("EP0007054A1")
    assert get_image.call_count == 3  # Both image alternatives returned 404.


@pytest.mark.parametrize("error_kind", ["json404", "http404", "json503"])
def test_odt_family_lookup_errors(dossier_data, monkeypatch, error_kind):
    from xml.etree import ElementTree

    from cornice.renderer import JSONError

    first_number = "EP0007054A1"
    second_number = "EP0666666A2"
    dossier_data["collections"]["rated"].append(
        {"number": second_number, "score": 1}
    )

    biblio = b"""\
<exchange-documents xmlns="http://www.epo.org/exchange">
  <exchange-document>
    <bibliographic-data>
      <invention-title lang="en">A test invention</invention-title>
      <applicant data-format="epodoc">
        <applicant-name><name>Test applicant</name></applicant-name>
      </applicant>
    </bibliographic-data>
    <abstract lang="en"><p>Test abstract</p></abstract>
  </exchange-document>
</exchange-documents>
"""
    request = SimpleNamespace(errors=["preexisting error"])
    monkeypatch.setattr(export, "get_current_request", lambda: request)
    monkeypatch.setattr(export, "get_ops_biblio_data", Mock(return_value=biblio))

    if error_kind == "http404":
        error = HTTPNotFound()
    else:
        error = JSONError(serializer=json.dumps, serializer_kw={}, errors=[])
        error.status = 404 if error_kind == "json404" else 503

    def get_family(number):
        if number == first_number:
            return SimpleNamespace(items=[])
        assert number == second_number
        request.errors.append("family lookup error")
        raise error

    family_lookup = Mock(side_effect=get_family)
    image_lookup = Mock(side_effect=HTTPNotFound())
    monkeypatch.setattr(export, "ops_family_members", family_lookup)
    monkeypatch.setattr(export, "get_ops_image", image_lookup)

    if error_kind == "json503":
        with pytest.raises(JSONError) as exc_info:
            export.DossierText(dossier_data).create()

        assert exc_info.value is error
        assert request.errors == ["preexisting error", "family lookup error"]
        return

    payload = export.DossierText(dossier_data).create()

    with ZipFile(BytesIO(payload)) as archive:
        assert archive.read("mimetype") == b"application/vnd.oasis.opendocument.text"
        content = ElementTree.fromstring(archive.read("content.xml"))
        text = " ".join(content.itertext())

    assert first_number in text
    assert second_number in text
    assert text.count("A test invention") == 2
    assert text.count("Test applicant") == 2
    assert text.count("Test abstract") == 2
    assert family_lookup.call_count == 2
    assert image_lookup.call_count == 6  # Both image alternatives for each card.
    assert request.errors == ["preexisting error"]


def test_odt_embeds_full_document_drawing_fallback(dossier_data, monkeypatch):
    from xml.etree import ElementTree

    from PIL import Image

    biblio = b"""\
<exchange-documents xmlns="http://www.epo.org/exchange">
  <exchange-document>
    <bibliographic-data>
      <invention-title lang="en">A test invention</invention-title>
    </bibliographic-data>
  </exchange-document>
</exchange-documents>
"""
    image_buffer = BytesIO()
    Image.new("RGB", (4, 4), "black").save(image_buffer, format="TIFF")
    image_bytes = image_buffer.getvalue()

    get_image = Mock(side_effect=[
        HTTPNotFound(),
        HTTPNotFound(),
        image_bytes,
    ])
    monkeypatch.setattr(export, "get_ops_biblio_data", Mock(return_value=biblio))
    monkeypatch.setattr(
        export, "ops_family_members", Mock(return_value=SimpleNamespace(items=[]))
    )
    monkeypatch.setattr(export, "get_ops_image", get_image)

    payload = export.DossierText(dossier_data).create()

    assert [entry.args[1:] for entry in get_image.call_args_list] == [
        (1, "FirstPageClipping", "png"),
        (1, "Drawing"),
        (1, "FullDocumentDrawing"),
    ]

    with ZipFile(BytesIO(payload)) as archive:
        content = ElementTree.fromstring(archive.read("content.xml"))
        image = content.find(
            ".//{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}image"
        )
        assert image is not None
        href = image.get("{http://www.w3.org/1999/xlink}href")
        assert href is not None
        assert archive.read(href) == image_bytes


def test_odt_document_ids(dossier_data, monkeypatch):
    from xml.etree import ElementTree

    biblio = b"""\
<exchange-documents xmlns="http://www.epo.org/exchange">
  <exchange-document>
    <bibliographic-data>
      <priority-claims>
        <priority-claim>
          <document-id document-id-type="epodoc">
            <doc-number>12345678</doc-number>
            <date>20200131</date>
          </document-id>
        </priority-claim>
        <priority-claim>
          <document-id document-id-type="epodoc">
            <doc-number>87654321</doc-number>
          </document-id>
        </priority-claim>
      </priority-claims>
      <application-reference>
        <document-id document-id-type="epodoc">
          <doc-number>11223344</doc-number>
          <date>20210215</date>
        </document-id>
        <document-id document-id-type="docdb">
          <doc-number>ignored-docdb-number</doc-number>
        </document-id>
      </application-reference>
      <publication-reference>
        <document-id document-id-type="epodoc">
          <doc-number>55667788</doc-number>
          <date>20220320</date>
        </document-id>
      </publication-reference>
    </bibliographic-data>
  </exchange-document>
</exchange-documents>
"""
    monkeypatch.setattr(export, "get_current_request", lambda: SimpleNamespace(errors=[]))
    monkeypatch.setattr(export, "get_ops_biblio_data", Mock(return_value=biblio))
    monkeypatch.setattr(
        export, "ops_family_members", Mock(return_value=SimpleNamespace(items=[]))
    )
    monkeypatch.setattr(export, "get_ops_image", Mock(side_effect=HTTPNotFound()))

    payload = export.DossierText(dossier_data).create()

    with ZipFile(BytesIO(payload)) as archive:
        content = ElementTree.fromstring(archive.read("content.xml"))

    text_namespace = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    paragraphs = [
        "".join(node.itertext())
        for node in content.iter(f"{{{text_namespace}}}p")
    ]

    expected_sections = {
        "Priority:": ["No 12345678 (2020-01-31)", "No 87654321 ()"],
        "Filing:": ["No 11223344 (2021-02-15)"],
        "Publication:": ["No 55667788 (2022-03-20)"],
    }
    for label, identifiers in expected_sections.items():
        start = paragraphs.index(label)
        assert paragraphs[start + 1 : start + 1 + len(identifiers)] == identifiers

    assert "ignored-docdb-number" not in " ".join(paragraphs)


def test_odt_contains_inventors(dossier_data, monkeypatch):
    from xml.etree import ElementTree

    biblio = b"""\
<exchange-documents xmlns="http://www.epo.org/exchange">
  <exchange-document>
    <bibliographic-data>
      <applicant data-format="epodoc">
        <applicant-name><name>Test Applicant</name></applicant-name>
      </applicant>
      <inventor data-format="epodoc">
        <inventor-name><name>Ada Inventor</name></inventor-name>
      </inventor>
      <inventor data-format="epodoc">
        <inventor-name><name>Grace Inventor</name></inventor-name>
      </inventor>
      <inventor data-format="docdb">
        <inventor-name><name>Ignored Inventor</name></inventor-name>
      </inventor>
    </bibliographic-data>
  </exchange-document>
</exchange-documents>
"""
    monkeypatch.setattr(
        export, "get_current_request", lambda: SimpleNamespace(errors=[])
    )
    monkeypatch.setattr(export, "get_ops_biblio_data", Mock(return_value=biblio))
    monkeypatch.setattr(
        export, "ops_family_members", Mock(return_value=SimpleNamespace(items=[]))
    )
    monkeypatch.setattr(export, "get_ops_image", Mock(side_effect=HTTPNotFound()))

    payload = export.DossierText(dossier_data).create()

    with ZipFile(BytesIO(payload)) as archive:
        content = ElementTree.fromstring(archive.read("content.xml"))

    ns = {"text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
    section = content.find(".//text:section[@text:name='Section1']", ns)
    assert section is not None

    paragraphs = [
        "".join(paragraph.itertext())
        for paragraph in section.findall("./text:p", ns)
    ]
    assert paragraphs.count("Inventor:") == 1
    index = paragraphs.index("Inventor:")
    assert paragraphs[index + 1:index + 3] == ["Ada Inventor", "Grace Inventor"]
    assert "Ignored Inventor" not in paragraphs


@pytest.mark.parametrize("scheme", ["CPCI", "CPC", "CPCNO"])
def test_odt_classifications(dossier_data, monkeypatch, scheme):
    from xml.etree import ElementTree

    def cpc(office):
        return f"""
        <patent-classification>
          <classification-scheme scheme="{scheme}" office="XX"/>
          <section>A</section>
          <class>01</class>
          <subclass>B</subclass>
          <main-group>1</main-group>
          <subgroup>00</subgroup>
          <generating-office>{office}</generating-office>
        </patent-classification>
        """

    def ipc(office):
        return f"""
        <patent-classification>
          <classification-scheme scheme="IPC" office="{office}"/>
          <classification-symbol>H01M10/0525</classification-symbol>
        </patent-classification>
        """

    biblio = f"""\
    <exchange-documents xmlns="http://www.epo.org/exchange">
      <exchange-document>
        <bibliographic-data>
          <patent-classifications>
            {cpc("EP")}
            {cpc("US")}
            {ipc("EP")}
            {ipc("WO")}
          </patent-classifications>
        </bibliographic-data>
      </exchange-document>
    </exchange-documents>
    """.encode("utf-8")

    monkeypatch.setattr(
        export, "get_current_request", lambda: SimpleNamespace(errors=[])
    )
    monkeypatch.setattr(export, "get_ops_biblio_data", Mock(return_value=biblio))
    monkeypatch.setattr(
        export, "ops_family_members", Mock(return_value=SimpleNamespace(items=[]))
    )
    monkeypatch.setattr(export, "get_ops_image", Mock(side_effect=HTTPNotFound()))

    payload = export.DossierText(dossier_data).create()

    with ZipFile(BytesIO(payload)) as archive:
        content = ElementTree.fromstring(archive.read("content.xml"))

    text_ns = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    paragraphs = [
        "".join(node.itertext())
        for node in content.iter(f"{{{text_ns}}}p")
    ]
    assert "Classification:" in paragraphs
    assert paragraphs.count("- A01B1/00 (EP, US)") == 1
    assert paragraphs.count("- H01M10/0525 (EP, WO)") == 1
