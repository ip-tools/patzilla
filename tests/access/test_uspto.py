# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Validate PDF document acquisition from USPTO servers.
"""
import re

import pytest
from bunch import Bunch
from pyramid.httpexceptions import HTTPNotFound

from patzilla.access.uspto.image import fetch_first_drawing
from patzilla.access.uspto.pdf import fetch_pdf, document_viewer_url, pdf_index, pdf_url, fetch_url, get_reference_type, \
    UsptoPdfReferenceType
from patzilla.util.numbers.common import split_patent_number


PDF_HEADER = b"%PDF"
TIFF_HEADER_LITTLE_ENDIAN = b"\x49\x49\x2a\x00"


class TestFetchResourceValid:

    # TODO: What about US design documents?
    #       Works: USD283336S, USD283316S
    #       Fails: USD283334S, USD283338S, USD283362S

    @pytest.mark.slow
    def test_full_pdf_application(self):
        # TODO: Find a smaller application document.
        pdf = fetch_pdf("US2022110447A1")
        assert pdf.startswith(PDF_HEADER)

    @pytest.mark.slow
    def test_full_pdf_publication(self):
        # US2548918 has only 240k, which is great for testing.
        pdf = fetch_pdf("US2548918")
        assert pdf.startswith(PDF_HEADER)

    @pytest.mark.slow
    def test_first_drawing_application(self):
        # TODO: Find a smaller application document.
        drawing = fetch_first_drawing("US2022110447A1")
        assert drawing.startswith(TIFF_HEADER_LITTLE_ENDIAN)

    @pytest.mark.slow
    def test_first_drawing_publication_patent(self):
        # US2548918 has only 240k, which is great for testing.
        drawing = fetch_first_drawing(split_patent_number("US2548918"))
        assert drawing.startswith(TIFF_HEADER_LITTLE_ENDIAN)

    @pytest.mark.slow
    def test_first_drawing_publication_design(self):
        # USD283349S has only 65k, which is great for testing.
        drawing = fetch_first_drawing(split_patent_number("USD283349S"))
        assert drawing.startswith(TIFF_HEADER_LITTLE_ENDIAN)


class TestFetchResourceInvalid:

    @pytest.mark.slow
    def test_full_pdf_application_notfound(self):
        with pytest.raises(HTTPNotFound) as ex:
            fetch_pdf("US0000000000")
        assert ex.match("Resource at .+ not found")

    @pytest.mark.slow
    def test_full_pdf_publication_notfound(self):
        with pytest.raises(HTTPNotFound) as ex:
            fetch_pdf("US0000000")
        assert ex.match("Resource at .+ not found")


class TestDocumentViewerUrlValid:

    @pytest.mark.slow
    def test_application_validated(self):
        assert document_viewer_url("US2022110447A1") == {'origin': 'USPTO', 'location': 'https://pdfaiw.uspto.gov/.aiw?docid=20220110447'}

    @pytest.mark.slow
    def test_publication_validated(self):
        assert document_viewer_url("US2548918") == {'origin': 'USPTO', 'location': 'https://pdfpiw.uspto.gov/.piw?docid=02548918'}

    def test_application_unvalidated(self):
        assert document_viewer_url("US2022110447A1", validate=False) == {'origin': 'USPTO', 'location': 'https://pdfaiw.uspto.gov/.aiw?docid=20220110447'}

    def test_publication_unvalidated(self):
        assert document_viewer_url("US2548918", validate=False) == {'origin': 'USPTO', 'location': 'https://pdfpiw.uspto.gov/.piw?docid=02548918'}


class TestDocumentViewerUrlInvalid:

    @pytest.mark.slow
    def test_application_validated(self):
        with pytest.raises(HTTPNotFound) as ex:
            document_viewer_url("US0000000000")
        ex.match("Resource at .+ not found")

    @pytest.mark.slow
    def test_publication_validated(self):
        with pytest.raises(HTTPNotFound) as ex:
            document_viewer_url("US0000000")
        ex.match("Resource at .+ not found")

    def test_application_unvalidated(self):
        assert document_viewer_url("US0000000000", validate=False) == {'origin': 'USPTO', 'location': 'https://pdfaiw.uspto.gov/.aiw?docid=00000000000'}

    def test_publication_unvalidated(self):
        assert document_viewer_url("US0000000", validate=False) == {'origin': 'USPTO', 'location': 'https://pdfpiw.uspto.gov/.piw?docid=00000000'}


def test_pdf_index_unknown_application(caplog):
    section_url_map = pdf_index("US2022110447A1", include=-99)
    assert not section_url_map
    assert "Unable to compute PDF section map for document US2022110447A1" in caplog.messages


def test_pdf_index_unknown_publication(caplog):
    section_url_map = pdf_index("US2548918", include=-99)
    assert not section_url_map
    assert "Unable to compute PDF section map for document US2548918" in caplog.messages


def test_pdf_url_invalid():
    assert pdf_url(None) is None


def test_fetch_url_failure():
    with pytest.raises(HTTPNotFound) as ex:
        assert fetch_url("https://httpbin.org/status/500") is None
    ex.match("Accessing resource at .+ failed. status=500, response=")


def test_get_reference_type_valid():
    assert get_reference_type(Bunch(number="2022110447")) == UsptoPdfReferenceType.APPLICATION
    assert get_reference_type(Bunch(number="2548918")) == UsptoPdfReferenceType.PUBLICATION
    assert get_reference_type(Bunch(number=1)) == UsptoPdfReferenceType.PUBLICATION


def test_get_reference_type_invalid():
    with pytest.raises(ValueError) as ex:
        get_reference_type(None)
    assert ex.match(re.escape("Unknown document reference type: None"))

    with pytest.raises(ValueError) as ex:
        get_reference_type(Bunch())
    assert ex.match(re.escape("Unknown document reference type:"))

    with pytest.raises(ValueError) as ex:
        get_reference_type(Bunch(number=None))
    assert ex.match(re.escape("Unknown document reference type:"))
