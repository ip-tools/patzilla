# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import json

from patzilla.access.dpma.dpmaregister import access_register
from patzilla.util.data.container import jpath


def test_dpmaregister_url_en():
    url = access_register("WO2008034638", output_format="url")
    assert url == "https://register.dpma.de/DPMAregister/pat/register:showalleverfahrenstabellen?AKZ=EP2007008279&lang=en"


def test_dpmaregister_url_de():
    url = access_register("WO2008034638", output_format="url", language="de")
    assert url == "https://register.dpma.de/DPMAregister/pat/register:showalleverfahrenstabellen?AKZ=EP2007008279&lang=de"


def test_dpmaregister_xml():
    xml = access_register("WO2008034638", output_format="xml")
    assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
    assert "<dpma-patent-document" in xml
    assert "<bibliographic-data>" in xml
    assert "<events>" in xml


def test_dpmaregister_json():
    data = json.loads(access_register("EP666666", output_format="json"))
    assert jpath("/application_reference/0/doc_number", data) == "69534171.5"
    assert jpath("/application_reference/1/doc_number", data) == "95480005.8"
    assert jpath("/title/text", data) == u"Verfahren und Vorrichtung für verbesserten Durchfluss in einem Vielfachknoten-Kommunikationssystem mit einem gemeinsamen Betriebsmittel"
    assert jpath("/designated_states", data) == ["DE", "FR", "GB"]
    assert jpath("/office_specific_bibdata/status", data) == "nicht-anhaengig-erloschen"
    assert len(jpath("/events", data)) == 11


def test_dpmaregister_html_compact_en():
    html = access_register("EP666666", output_format="html-compact")
    assert "EPO 1st publication" in html
    assert "Aug 9, 1995" in html


def test_dpmaregister_html_compact_de():
    html = access_register("EP666666", output_format="html-compact", language="de")
    print(html)
    assert "EPA-Erstveröffentlichung" in html
    assert "09.08.1995" in html


def test_dpmaregister_pdf_compact_en():
    pdf = access_register("EP666666", output_format="pdf")
    assert "File number 695 34 171.5" in pdf
    assert "Most recent update in DPMAregister on Jan 7, 2017" in pdf


def test_dpmaregister_pdf_compact_de():
    pdf = access_register("EP666666", output_format="pdf", language="de")
    assert "Aktenzeichen 695 34 171.5" in pdf
    assert "letzte Aktualisierung in DPMAregister am 07.01.2017" in pdf
