from patzilla.util.numbers.numberlists import parse_numberlist, normalize_numbers


def test_parse_numberlist():
    """
    Proof that conveniently parsing a list of items works.
    """
    assert parse_numberlist(u"foo , bar") == [u'foo', u'bar']
    assert parse_numberlist(u"foo \n bar") == [u'foo', u'bar']


def test_normalize_numbers_valid():
    """
    Normalize a list of valid patent numbers.
    """
    assert normalize_numbers([u'EP666666B1', u'EP1000000']) == {'all': [u'EP0666666B1', u'EP1000000'], 'invalid': [], 'valid': [u'EP0666666B1', u'EP1000000']}


def test_normalize_numbers_invalid():
    """
    Normalize a list of invalid patent numbers.
    """
    assert normalize_numbers([u'foo', u'bar']) == {'all': [u'foo', u'bar'], 'invalid': [u'foo', u'bar'], 'valid': []}


def test_normalize_numbers_mixed():
    """
    Normalize a list of both valid and invalid patent numbers.
    """
    assert normalize_numbers([u'EP666666B1', u'foobar']) == {'all': [u'EP0666666B1', u'foobar'], 'invalid': [u'foobar'], 'valid': [u'EP0666666B1']}
