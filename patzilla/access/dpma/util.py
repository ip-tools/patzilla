# -*- coding: utf-8 -*-
# (c) 2017 The PatZilla authors

def dpma_file_number(document_number):
    """
    Compute DPMA file number (Aktenzeichen) from DE publication/application number
    by calculating the checksum of the document number.

    See also section 4 in https://www.dpma.de/docs/dpma/veroeffentlichungen/dpmainformativ_nr05.pdf


    # Just append checksum for document numbers starting with "DE"
    >>> dpma_file_number('DE10001499')
    '100014992'

    # If there's probably already a checksum, use it
    >>> dpma_file_number('DE10001499.2')
    '100014992'


    # ... for all others, return them verbatim.
    >>> dpma_file_number('10001499')
    '10001499'

    >>> dpma_file_number('10001499.2')
    '10001499.2'

    >>> dpma_file_number('EP666666')
    'EP666666'
    """

    if document_number.startswith('DE'):

        docno_numeric = document_number[2:]

        # If document number contains a dot, assume it's
        # the checksum digit following it and we're finished.
        if '.' in docno_numeric:
            file_number = docno_numeric.replace('.', '')

        # Compute and append checksum digit according to specification (see PDF link above).
        else:

            if not docno_numeric.isdigit():
                raise ValueError('Document number "{}" is not numeric'.format(docno_numeric))

            checksum = 0
            for i, n in enumerate(reversed(docno_numeric)):
                checksum += int(n, 10) * (i + 2)
            checksum = checksum % 11
            if checksum:
                checksum = 11 - checksum

            file_number = docno_numeric + str(checksum)

        return file_number

    # If it's not suitable for this algorithm, return document number unchanged
    return document_number
