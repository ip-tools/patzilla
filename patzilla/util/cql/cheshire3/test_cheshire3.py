# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import unittest
from patzilla.util.cql.cheshire3.parser import parse as cql_parse, Diagnostic


class TestCheshire3CqlParser(unittest.TestCase):

    suppress_stacktraces = True

    def do_parse(self, query):
        query_object = cql_parse(query)
        query_parsed = query_object.toCQL().strip()
        #print query.ljust(40), '\t', query_parsed
        return query_parsed

    def test_simple(self):
        self.assertEqual(self.do_parse('pn=foo'), 'pn = "foo"')

    def test_simple_bool(self):
        self.assertEqual(self.do_parse('pn=foo and pc=bar'), '(pn = "foo" and pc = bar)')

    def test_simple_quotes(self):
        self.assertEqual(self.do_parse('pn="foo" and pc=bar'), '(pn = "foo" and pc = bar)')

    def test_simple_multiple(self):
        self.assertEqual(self.do_parse('ti=foo and ti=bar and pc=qux'), '((ti = "foo" and ti = "bar") and pc = qux)')

    def test_nested(self):
        self.assertEqual(self.do_parse(
            '(bi=foo and (bi=bar or bi=baz)) and pc=qux'),
            '((bi = "foo" and (bi = "bar" or bi = "baz")) and pc = qux)')

    def test_value_parentheses(self):
        self.assertEqual(self.do_parse('pn=(foo) and pc=bar'), '(pn = "foo" and pc = bar)')

    def test_value_shortcut_notation_two(self):
        self.assertEqual(self.do_parse(
            'ti=(foo and bar) and pc=qux'),
            '((ti = "foo" and ti = "bar") and pc = qux)')

    def test_value_shortcut_notation_two_right(self):
        self.assertEqual(self.do_parse(
            'pc=qux and ti=(foo and bar)'),
            '(pc = qux and (ti = "foo" and ti = "bar"))')

    def test_value_shortcut_notation_three(self):
        self.assertEqual(self.do_parse(
            'ti=(foo and bar and baz) and pc=qux'),
            '(((ti = "foo" and ti = "bar") and ti = "baz") and pc = qux)')

    def test_value_shortcut_notation_fail(self):
        with self.assertRaises(Diagnostic) as cm:
            self.do_parse('ti=(foo and bar baz) and pc=qux')
        self.assertEqual(
            str(cm.exception),
            "info:srw/diagnostic/1/10 [Malformed Query]: Expected Boolean or closing parenthesis but got: u'baz'")

    def test_boolean_german(self):
        self.assertEqual(self.do_parse('bi=foo und bi=bar'), '(bi = "foo" und bi = "bar")')

    def test_utf8(self):
        self.assertEqual(self.do_parse('ab=radaufstandskraft or ab=radaufstandskräfte?'), u'(ab = "radaufstandskraft" or ab = "radaufstandskr\xe4fte?")')

if __name__ == '__main__':
    unittest.main()
