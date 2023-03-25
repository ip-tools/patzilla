from patzilla.util.numbers.numberlists import parse_numberlist, normalize_numbers


def test_parse_numberlist():
    """
    Proof that conveniently parsing a list of items works.
    """
    assert parse_numberlist("foo , bar") == ['foo', 'bar']
    assert parse_numberlist("foo \n bar") == ['foo', 'bar']


def test_normalize_numbers_valid():
    """
    Normalize a list of valid patent numbers.
    """
    assert normalize_numbers(['EP666666B1', 'EP1000000']) == {'all': ['EP0666666B1', 'EP1000000'], 'invalid': [], 'valid': ['EP0666666B1', 'EP1000000']}


def test_normalize_numbers_invalid():
    """
    Normalize a list of invalid patent numbers.
    """
    assert normalize_numbers(['foo', 'bar']) == {'all': ['foo', 'bar'], 'invalid': ['foo', 'bar'], 'valid': []}


def test_normalize_numbers_mixed():
    """
    Normalize a list of both valid and invalid patent numbers.
    """
    assert normalize_numbers(['EP666666B1', 'foobar']) == {'all': ['EP0666666B1', 'foobar'], 'invalid': ['foobar'], 'valid': ['EP0666666B1']}
