# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl <andreas.motl@ip-tools.org>
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse

from patzilla.util.numbers.normalize import normalize_patent

router = APIRouter(include_in_schema=False)


@router.get('/office/{office}/{service}/{document_type}/{document_number}', name='jump-office')
def jump_office(office: str, service: str, document_type: str, document_number: str, redirect: str = None):
    """Redirect to, or respond with, the URL of a document at a patent office or other service."""

    if document_number:

        url = None
        if office == 'dpma' and service == 'register':
            from patzilla.access.dpma.dpmaregister import DpmaRegisterAccess
            dra = DpmaRegisterAccess()
            try:
                url = dra.get_document_url(document_number)
            except:
                raise HTTPException(404, 'Document number {} not found.'.format(document_number))

            # TODO: application number vs. file number, e.g.
            # - EP666666   vs. E95480005.8
            # - DE19630877 vs. 196308771

        elif office == 'uspto' and service == 'biblio':

            if document_type == 'publication':
                # http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO1&Sect2=HITOFF&d=PALL&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.htm&r=1&f=G&l=50&s1=9317610
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'https://patft.uspto.gov/netacgi/nph-Parser'\
                      '?Sect1=PTO1&Sect2=HITOFF&d=PALL&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.htm&r=1&f=G&l=50&s1={number}.PN.'.format(**document)

            elif document_type == 'application':
                # http://appft.uspto.gov/netacgi/nph-Parser?Sect1=PTO1&Sect2=HITOFF&d=PG01&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.html&r=1&f=G&l=50&s1=20160105912
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'https://appft.uspto.gov/netacgi/nph-Parser'\
                      '?Sect1=PTO1&Sect2=HITOFF&d=PG01&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.html&r=1&f=G&l=50&s1={number}'.format(**document)

        elif office == 'uspto' and service == 'images':

            if document_type == 'publication':
                # https://pdfpiw.uspto.gov/.piw?docid=9317610
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'https://pdfpiw.uspto.gov/.piw?docid={number}'.format(**document)

            elif document_type == 'application':
                # https://pdfaiw.uspto.gov/.aiw?docid=20160105912
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'https://pdfaiw.uspto.gov/.aiw?docid={number}'.format(**document)

        elif office == 'uspto' and service == 'global-dossier':
            # https://globaldossier.uspto.gov/#/result/publication/DE/112015004959/1
            normalized = normalize_patent(document_number, as_dict=True, for_ops=False)
            url = 'https://globaldossier.uspto.gov/#/result/{document_type}/{country}/{number}/1'.format(
                document_type=document_type, **normalized)

        elif office == 'google' and service == 'patents':
            # https://www.google.com/patents/EP0666666B1
            # https://patents.google.com/patent/EP0666666B1
            normalized = normalize_patent(document_number, for_ops=False)
            url = 'https://patents.google.com/patent/{}'.format(normalized)

        # Add Google Prior Art search again. See "priorArtKeywords" and "priorArtDate" in HTML response.

        if url:
            if redirect:
                return RedirectResponse(url, status_code=302)
            else:
                return PlainTextResponse(url)

    raise HTTPException(404, 'Could not locate document "{document_number}" at {office}/{service}.'.format(
        document_number=document_number, office=office, service=service))
