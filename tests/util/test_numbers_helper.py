# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
from mock.mock import patch, mock_open

from patzilla.util.numbers.helper import read_numbersfile


def test_read_numbersfile():
    data = """
# A list of document numbers in text form.
# Reference: dda5b08e-78b0-4b20-b291-f105205a3fc4
 EP666666

\tEP666667
\r\n
EP666668;
'"EP666669"'

"""
    # TODO: Need to adjust for Python 3, see https://stackoverflow.com/a/34677735.
    with patch("builtins.open", mock_open(read_data=data)) as mock_file:
        numbers = read_numbersfile(None)
    assert numbers == ['EP666666', 'EP666667', 'EP666668', 'EP666669']
