# -*- coding: utf-8 -*-

from patzilla.util.text.format import slugify, text_indent


def test_slugify():
    assert slugify("Franz jagt Trueffel.") == "franz-jagt-trueffel"
    assert slugify(u"Franz jagt Trüffel -=- im Wald. 👋") == "franz-jagt-truffel-im-wald"
    assert slugify(u"Franz jagt Trüffel -=- im Wald. 👋", strip_equals=False) == "franz-jagt-truffel-=-im-wald"
    assert slugify(u"Franz jagt Trüffel -=- im Wald. 👋", lowercase=False) == "Franz-jagt-Truffel-im-Wald"


def test_text_indent():
    assert text_indent(u"Franz jagt Trüffel.\nIm Wald.\n\n👋") == u"""
    Franz jagt Trüffel.
    Im Wald.
    
    👋
    """.lstrip("\n").rstrip()
