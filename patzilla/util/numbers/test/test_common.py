# -*- coding: utf-8 -*-
# (c) 2009,2015 Andreas Motl <andreas.motl@elmyra.de>
from collections import OrderedDict

import pytest

from patzilla.util.numbers.common import split_patent_number


good = OrderedDict()
good['USRE039998E1']     = {'kind': 'E1', 'country': 'US', 'number': 'RE039998', 'number-type': 'RE', 'ext': '', 'number-real': '039998'}
good['BR000PI0502229A']  = {'country': 'BR', 'kind': 'A',  'ext': '', 'number': '000PI0502229'}
good['ITVR0020130124A']  = {'kind': 'A', 'country': 'IT', 'number': 'VR0020130124', 'number-type': 'VR', 'ext': '', 'number-real': '0020130124'}


bad = OrderedDict()
bad['WO2003EP8824']      = None
bad['IT19732A88']        = None
bad['JPHEI 3-53606']     = None


def generate(data):
    for number, number_normalized_expect in data.items():
        number_normalized_computed = split_patent_number(number)
        yield number, number_normalized_expect, number_normalized_computed


class TestNumberDecoding:

    @pytest.mark.parametrize("number,expected,computed", generate(good), ids=good.keys())
    def testDecodeOK(self, number, expected, computed):
        self.check_ok(number, expected, computed)

    @pytest.mark.parametrize("number,expected,computed", generate(bad), ids=bad.keys())
    def testDecodeBAD(self, number, expected, computed):
        self.check_ok(number, expected, computed)

    def check_ok(self, number, expected, computed):
        assert computed == expected, "number: %s, expected: %s, computed: %s" % (number, expected, computed)

    #def check_fail(self, ipc_class):
    #    IpcDecoder(ipc_class['raw'])
