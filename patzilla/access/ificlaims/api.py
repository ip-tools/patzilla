# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
#
# Highlevel adapter to search provider "IFI CLAIMS Direct"
#
import json
import logging
from collections import OrderedDict
from patzilla.access.ificlaims.client import ificlaims_fetch, IFIClaimsException
from patzilla.util.numbers.common import split_patent_number
from patzilla.util.python import _exception_traceback
from patzilla.util.xml.format import pretty_print

logger = logging.getLogger(__name__)

class IFIClaimsDocumentIdentifier(object):

    def __init__(self, original):
        self.original = original
        self.compute()

    def compute(self):
        self.document = split_patent_number(self.original)

    def normalize_ucid(self):
        country = self.document['country']
        number = self.document['number']
        kind = self.document['kind']

        if country == 'EP':
            number = number.rjust(7, '0')

        self.document['country'] = country
        self.document['number'] = number
        self.document['kind'] = kind

    def format_ucid(self):
        self.normalize_ucid()
        ucid = '-'.join([self.document['country'], self.document['number'], self.document['kind']])
        return ucid

    def format_ucid_natural(self):
        self.normalize_ucid()
        ucid = ''.join([self.document['country'], self.document['number'], self.document['kind']])
        return ucid

class IFIClaimsDocumentResponse(object):

    # for wich mimetypes to deliver "Content-Disposition: inline; ..." responses
    inline_mimetypes = [
        'text/xml',
        'application/json',
        'application/pdf',
        'image/png',
    ]

    def __init__(self):
        self.mimetype = None
        self.filename = None
        self.payload = None
        self.ucid = None
        self.ucid_natural = None

    @property
    def disposition_inline(self):
        if self.mimetype in self.inline_mimetypes:
            return True
        else:
            return False

class IFIClaimsDocumentRequest(object):

    def __init__(self, identifier, format, options=None):
        options = options or {}
        self.identifier = identifier
        self.format = format
        self.options = options

        identifier = IFIClaimsDocumentIdentifier(identifier)
        self.ucid = identifier.format_ucid()
        self.ucid_natural = identifier.format_ucid_natural()

        self.response = IFIClaimsDocumentResponse()
        self.response.ucid = self.ucid
        self.response.ucid_natural = self.ucid_natural

    def download(self):

        if self.format in ['tif', 'png']:
            self.options.setdefault('seq', 1)

        self.response.payload = ificlaims_fetch(self.ucid, self.format, self.options)

        name_suffix = ''
        if self.format == 'xml':
            self.response.mimetype = 'text/xml'
            file_suffix = 'xml'

        elif self.format == 'json':
            self.response.mimetype = 'application/json'
            file_suffix = 'json'

        elif self.format == 'pdf':
            self.response.mimetype = 'application/pdf'
            file_suffix = 'pdf'

        elif self.format == 'tif':
            self.response.mimetype = 'image/tiff'
            file_suffix = 'tif'
            name_suffix = '-{seq}'.format(seq=self.options['seq'])

        elif self.format == 'png':
            self.response.mimetype = 'image/png'
            file_suffix = 'png'
            name_suffix = '-{seq}'.format(seq=self.options['seq'])

        else:
            self.response.mimetype = 'application/octet-stream'
            file_suffix = self.format

        self.response.filename = '{ucid_natural}{name_suffix}.{suffix}'.format(
            ucid_natural=self.ucid_natural, name_suffix=name_suffix, suffix=file_suffix)

        return self

    def transform(self):

        if not self.response.payload:
            return self

        if self.options.get('pretty', False):
            if self.format == 'xml':
                self.response.payload = pretty_print(self.response.payload)
            elif self.format == 'json':
                self.response.payload = json.dumps(json.loads(self.response.payload), indent=4)

        return self


def ificlaims_download(resource, format, options=None):
    options = options or {}
    logger.info('ificlaims_download: resource={resource}, format={format}, options={options}'.format(**locals()))
    r = IFIClaimsDocumentRequest(resource, format, options=options)
    return r.download().transform().response


def ificlaims_download_multi(numberlist, formats):

    logger.info('ificlaims_download_multi: numberlist={numberlist}, formats={formats}'.format(**locals()))

    report = OrderedDict()
    results = []

    for number in numberlist:

        report.setdefault(number, OrderedDict({'format': OrderedDict()}))

        for format in formats:

            format_parts = format.split(u':')

            # decode modifiers
            if len(format_parts) == 1:
                format_real = format
                modifiers = []
            else:
                format_real = format_parts[0]
                modifiers = format_parts[1:]

            # initialize availability status
            report[number]['format'][format_real] = False

            # compute options
            options = {}
            if 'pretty' in modifiers:
                options['pretty'] = True

            # collect nested documents, i.e. multiple drawings
            if format_real in ['tif', 'png']:
                count = 0
                try:
                    result_first = ificlaims_download_single(number, format_real, options)
                except Exception as ex:
                    logger.error('IFI: {ex}\n{traceback}'.format(ex=ex, traceback=_exception_traceback()))
                    continue

                if result_first:
                    report[number]['format'][format_real] = True
                    report[number]['ucid'] = result_first.ucid
                    report[number]['ucid-natural'] = result_first.ucid_natural
                    results.append(result_first.__dict__)
                    count += 1

                    # fetch more drawings until exhaust
                    for seq in range(2, 50):
                        options['seq'] = seq
                        try:
                            result_next = ificlaims_download_single(number, format_real, options)
                        except Exception as ex:
                            logger.error('IFI: {ex}\n{traceback}'.format(ex=ex, traceback=_exception_traceback()))
                            break

                        if not result_next:
                            break

                        results.append(result_next.__dict__)
                        count += 1

                report[number].setdefault('count', OrderedDict())
                report[number]['count'][format_real] = count

            else:
                try:
                    result_single = ificlaims_download_single(number, format_real, options)

                except Exception as ex:
                    logger.error('IFI: {ex}\n{traceback}'.format(ex=ex, traceback=_exception_traceback()))
                    continue

                if result_single:
                    report[number]['format'][format_real] = True
                    report[number]['ucid'] = result_single.ucid
                    report[number]['ucid-natural'] = result_single.ucid_natural
                    results.append(result_single.__dict__)


    response = {
        'report': report,
        'results': results,
    }
    return response

def ificlaims_download_single(number, format, options=None):

    try:
        response = ificlaims_download(number, format, options)

    except IFIClaimsException, ex:
        logger.warn('IFI: IFIClaimsException for number={number}, format={format}, options={options}: {ex}'.format(**locals()))

    if response.payload:
        return response

    else:
        logger.warn('IFI: Empty response for number={number}, format_real={format}'.format(**locals()))
