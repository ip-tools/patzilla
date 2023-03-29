# -*- coding: utf-8 -*-

from patzilla.util.text.format import slugify, text_indent


def test_slugify():
    assert slugify("Franz jagt Trueffel.") == b"franz-jagt-trueffel"
    assert slugify("Franz jagt Trüffel -=- im Wald. 👋") == b"franz-jagt-truffel-im-wald"
    assert slugify("Franz jagt Trüffel -=- im Wald. 👋", strip_equals=False) == b"franz-jagt-truffel-=-im-wald"
    assert slugify("Franz jagt Trüffel -=- im Wald. 👋", lowercase=False) == b"Franz-jagt-Truffel-im-Wald"


def test_text_indent():
    assert text_indent("Franz jagt Trüffel.\nIm Wald.\n\n👋") == """
    Franz jagt Trüffel.
    Im Wald.
    
    👋
    """.lstrip("\n").rstrip()
