# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import json

import pytest

from patzilla.access.dpma.dpmaregister import access_register
from patzilla.util.data.container import jpath


class F5WafWrapper:
    """
    As of 2022, DPMAregister is protected by a web application firewall.
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        error_message = str(exc_val)
        if exc_type is ValueError and error_message == "Site is protected by F5 Advanced WAF":
            raise pytest.skip(error_message)


def test_dpmaregister_url_en():
    with F5WafWrapper():
        url = access_register("EP666666", output_format="url")
        assert url == "https://register.dpma.de/DPMAregister/pat/register:showalleverfahrenstabellen?AKZ=E954800058&lang=en"


def test_dpmaregister_url_de():
    with F5WafWrapper():
        url = access_register("EP666666", output_format="url", language="de")
        assert url == "https://register.dpma.de/DPMAregister/pat/register:showalleverfahrenstabellen?AKZ=E954800058&lang=de"


def test_dpmaregister_xml():
    with F5WafWrapper():
        xml = access_register("EP666666", output_format="xml")
        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
        assert "<dpma-patent-document" in xml
        assert "<bibliographic-data>" in xml
        assert "<events>" in xml


def test_dpmaregister_json():
    with F5WafWrapper():
        data = json.loads(access_register("EP666666", output_format="json"))
        assert jpath("/application_reference/0/doc_number", data) == "69534171.5"
        assert jpath("/application_reference/1/doc_number", data) == "95480005.8"
        assert jpath("/title/text", data) == u"Verfahren und Vorrichtung für verbesserten Durchfluss in einem Vielfachknoten-Kommunikationssystem mit einem gemeinsamen Betriebsmittel"
        assert jpath("/designated_states", data) == ["DE", "FR", "GB"]
        assert jpath("/office_specific_bibdata/status", data) == "nicht-anhaengig-erloschen"
        assert len(jpath("/events", data)) == 11


def test_dpmaregister_html_compact_en():
    with F5WafWrapper():
        html = access_register("EP666666", output_format="html-compact")
        assert "EPO 1st publication" in html
        assert "Aug 9, 1995" in html


def test_dpmaregister_html_compact_de():
    with F5WafWrapper():
        html = access_register("EP666666", output_format="html-compact", language="de")
        print(html)
        assert "EPA-Erstveröffentlichung" in html
        assert "09.08.1995" in html


def test_dpmaregister_pdf_compact_en():
    with F5WafWrapper():
        pdf = access_register("EP666666", output_format="pdf")
        assert "File number 695 34 171.5" in pdf
        assert "Most recent update in DPMAregister on Jan 7, 2017" in pdf


def test_dpmaregister_pdf_compact_de():
    with F5WafWrapper():
        pdf = access_register("EP666666", output_format="pdf", language="de")
        assert "Aktenzeichen 695 34 171.5" in pdf
        assert "letzte Aktualisierung in DPMAregister am 07.01.2017" in pdf
