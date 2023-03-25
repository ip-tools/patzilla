# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Validate PDF document acquisition from USPTO servers.
"""
import re

import pytest
from munch import Munch
from pyramid.httpexceptions import HTTPNotFound

from patzilla.access.uspto.image import fetch_first_drawing
from patzilla.access.uspto.pdf import fetch_pdf, document_viewer_url, png_url, fetch_url, get_reference_type, \
    UsptoPdfReferenceType, UsptoPdfSection, UsptoDocumentAccess
from patzilla.util.numbers.common import split_patent_number


PDF_HEADER = b"%PDF"
PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
TIFF_HEADER_LITTLE_ENDIAN = b"\x49\x49\x2a\x00"


class TestFetchResourceValid:

    # TODO: What about US design documents?
    #       Works: USD283336S, USD283316S
    #       Fails: USD283334S, USD283338S, USD283362S

    @pytest.mark.slow
    def test_full_pdf_application(self):
        pdf = fetch_pdf("US20140071638A1")
        assert pdf.startswith(PDF_HEADER)

    @pytest.mark.slow
    def test_full_pdf_publication(self):
        # US2548918 has only 240k, which is great for testing.
        pdf = fetch_pdf("US2548918")
        assert pdf.startswith(PDF_HEADER)

    @pytest.mark.slow
    def test_first_drawing_application(self):
        drawing = fetch_first_drawing("US20140071638A1")
        assert drawing.startswith(PNG_HEADER)

    @pytest.mark.slow
    def test_first_drawing_publication_patent(self):
        # US2548918 has only 240k, which is great for testing.
        drawing = fetch_first_drawing(split_patent_number("US2548918"))
        assert drawing.startswith(PNG_HEADER)

    @pytest.mark.slow
    def test_first_drawing_publication_design(self):
        # USD283349S has only 65k, which is great for testing.
        drawing = fetch_first_drawing(split_patent_number("USD283349S"))
        assert drawing.startswith(PNG_HEADER)


class TestFetchResourceInvalid:

    @pytest.mark.slow
    def test_full_pdf_application_notfound_zero(self):
        with pytest.raises(HTTPNotFound) as ex:
            fetch_pdf("US0000000000")
        assert ex.match("Resource .+ not found")

    @pytest.mark.slow
    def test_full_pdf_publication_notfound_zero(self):
        with pytest.raises(HTTPNotFound) as ex:
            fetch_pdf("US0000000")
        assert ex.match("Resource .+ not found")

    @pytest.mark.slow
    def test_full_pdf_application_notfound_one(self):
        with pytest.raises(HTTPNotFound) as ex:
            fetch_pdf("US0000000001")
        assert ex.match("Resource .+ not found")

    @pytest.mark.slow
    def test_full_pdf_publication_notfound_one(self):
        with pytest.raises(HTTPNotFound) as ex:
            fetch_pdf("US0000001")
        assert ex.match("Resource .+ not found")


class TestDocumentViewerUrlValid:

    @pytest.mark.slow
    def test_application(self):
        assert document_viewer_url("US2022110447A1") == {
            'origin': 'USPTO',
            'location': 'https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=us-pgpub/US/2022/0110/447/00000001.tif',
        }

    @pytest.mark.slow
    def test_publication(self):
        assert document_viewer_url("US2548918") == {
            'origin': 'USPTO',
            'location': 'https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/02/548/918/00000001.tif',
        }


class TestDocumentViewerUrlInvalid:

    @pytest.mark.slow
    def test_application_zeros(self):
        with pytest.raises(HTTPNotFound) as ex:
            document_viewer_url("US0000000000")
        ex.match("Resource .+ not found")

    @pytest.mark.slow
    def test_publication_zeros(self):
        with pytest.raises(HTTPNotFound) as ex:
            document_viewer_url("US0000000")
        ex.match("Resource .+ not found")

    @pytest.mark.slow
    def test_application_one(self):
        with pytest.raises(HTTPNotFound) as ex:
            document_viewer_url("US0000000001")
        ex.match("Resource .+ not found")

    @pytest.mark.slow
    def test_publication_one(self):
        with pytest.raises(HTTPNotFound) as ex:
            document_viewer_url("US0000001")
        ex.match("Resource .+ not found")


def test_pdf_index_application_valid(caplog):
    section_url_map = UsptoDocumentAccess("US20140071638A1").pdf_index()
    assert section_url_map[UsptoPdfSection.DRAWINGS] == \
           "https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=us-pgpub/US/2014/0071/638/00000002.tif"


def test_pdf_index_publication_valid(caplog):
    section_url_map = UsptoDocumentAccess("US2548918").pdf_index()
    assert section_url_map[UsptoPdfSection.DRAWINGS] == \
           "https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/02/548/918/00000001.tif"


def test_pdf_index_application_unknown(caplog):
    section_url_map = UsptoDocumentAccess("US2022110447A1").pdf_index(include=-99)
    assert not section_url_map
    assert "Unable to compute PDF section map for document US2022110447A1" in caplog.messages


def test_pdf_index_publication_unknown(caplog):
    section_url_map = UsptoDocumentAccess("US2548918").pdf_index(include=-99)
    assert not section_url_map
    assert "Unable to compute PDF section map for document US2548918" in caplog.messages


def test_pdf_url_invalid():
    assert png_url(None) is None


def test_fetch_url_failure():
    with pytest.raises(HTTPNotFound) as ex:
        assert fetch_url("https://httpbin.org/status/500") is None
    ex.match("Accessing resource at .+ failed. status=500, response=")


def test_get_reference_type_valid():
    assert get_reference_type(Munch(number="2022110447")) == UsptoPdfReferenceType.APPLICATION
    assert get_reference_type(Munch(number="2548918")) == UsptoPdfReferenceType.PUBLICATION
    assert get_reference_type(Munch(number=1)) == UsptoPdfReferenceType.PUBLICATION


def test_get_reference_type_invalid():
    with pytest.raises(ValueError) as ex:
        get_reference_type(None)
    assert ex.match(re.escape("Unknown document reference type: None"))

    with pytest.raises(ValueError) as ex:
        get_reference_type(Munch())
    assert ex.match(re.escape("Unknown document reference type:"))

    with pytest.raises(ValueError) as ex:
        get_reference_type(Munch(number=None))
    assert ex.match(re.escape("Unknown document reference type:"))
