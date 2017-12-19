# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from patzilla.access.dpma.dpmaregister import DpmaRegisterAccess
from patzilla.util.numbers.normalize import normalize_patent

def includeme(config):
    config.add_route('jump-office', '/office/{office}/{service}/{document_type}/{document_number}')

@view_config(route_name='jump-office')
def jump_office(request):
    office          = request.matchdict.get('office')
    service         = request.matchdict.get('service')
    document_type   = request.matchdict.get('document_type')
    document_number = request.matchdict.get('document_number')
    redirect        = request.params.get('redirect')

    if document_number:

        url = None
        if office == 'dpma' and service == 'register':
            dra = DpmaRegisterAccess()
            try:
                url = dra.get_document_url(document_number)
            except:
                return HTTPNotFound('Document number {} not found.'.format(document_number))

            # TODO: application number vs. file number, e.g.
            # - EP666666   vs. E95480005.8
            # - DE19630877 vs. 196308771

        elif office == 'uspto' and service == 'biblio':

            if document_type == 'publication':
                # http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO1&Sect2=HITOFF&d=PALL&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.htm&r=1&f=G&l=50&s1=9317610
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'http://patft.uspto.gov/netacgi/nph-Parser'\
                      '?Sect1=PTO1&Sect2=HITOFF&d=PALL&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.htm&r=1&f=G&l=50&s1={number}.PN.'.format(**document)

            elif document_type == 'application':
                # http://appft.uspto.gov/netacgi/nph-Parser?Sect1=PTO1&Sect2=HITOFF&d=PG01&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.html&r=1&f=G&l=50&s1=20160105912
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'http://appft.uspto.gov/netacgi/nph-Parser'\
                      '?Sect1=PTO1&Sect2=HITOFF&d=PG01&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.html&r=1&f=G&l=50&s1={number}'.format(**document)

        elif office == 'uspto' and service == 'images':

            if document_type == 'publication':
                # http://pdfpiw.uspto.gov/.piw?docid=9317610
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'http://pdfpiw.uspto.gov/.piw?docid={number}'.format(**document)

            elif document_type == 'application':
                # http://pdfaiw.uspto.gov/.aiw?docid=20160105912
                document = normalize_patent(document_number, as_dict=True, for_ops=False)
                url = 'http://pdfaiw.uspto.gov/.aiw?docid={number}'.format(**document)

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
                return HTTPFound(location=url)
            else:
                return url

    return HTTPNotFound(u'Could not locate document "{document_number}" at {office}/{service}.'.format(
        document_number=document_number, office=office, service=service))
