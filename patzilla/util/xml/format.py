# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG
from lxml import etree

# https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python/12940014#12940014
import re
from xmljson import BadgerFish

def etree_indent(elem, level=0, more_sibs=False):
    i = "\n"
    spacing = '    '
    if level:
        i += (level-1) * spacing
    num_kids = len(elem)
    if num_kids:
        if not elem.text or not elem.text.strip():
            elem.text = i + spacing
            if level:
                elem.text += spacing
        count = 0
        for kid in elem:
            etree_indent(kid, level+1, count < num_kids - 1)
            count += 1
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
            if more_sibs:
                elem.tail += spacing
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
            if more_sibs:
                elem.tail += spacing

def pretty_print(xml, xml_declaration=True):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml, parser)

    # pretty print xml
    etree_indent(root)

    # 2016-01-06: deactivated again, makes problems
    #xml = etree.tostring(root, encoding='utf-8', xml_declaration=xml_declaration, pretty_print=True)

    xml = etree.tostring(root, pretty_print=True)
    xml = xml.strip()

    return xml

def compact_print(xml):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml, parser)
    xml = etree.tostring(root)
    xml = xml.strip()
    return xml


class BadgerFishNoNamespace(BadgerFish):

    def data(self, root):
        """Convert etree.Element into a dictionary while completely ignoring xml namespaces"""

        # Clean tag name of root element
        self.clean_tag(root)

        # Clean tag name of all child elements
        for node in root:
            self.clean_tag(node)

        return super(BadgerFishNoNamespace, self).data(root)

    def clean_tag(self, node):
        if isinstance(node.tag, basestring):
            node.tag = re.sub('{.*}', '', node.tag)
