# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG
import re

from lxml import etree, objectify
from xmljson import BadgerFish


def etree_indent(elem, level=0, more_sibs=False):
    """
    Pretty printing XML in Python.

    https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python/12940014#12940014
    """
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
        self.eliminate_namespaces(root)

        # Clean tag name of all child elements
        for node in root:
            self.eliminate_namespaces(node)

        return super(BadgerFishNoNamespace, self).data(root)

    def eliminate_namespaces(self, node):
        if isinstance(node.tag, str):
            node.tag = self.replace_namespace(node.tag)

        for attr in node.attrib:
            value = node.attrib.get(attr)
            if attr.startswith("{"):
                node.attrib.pop(attr)
            attr_name = self.replace_namespace(attr)
            node.attrib.update({attr_name: value})

    def replace_namespace(self, data):
        return re.sub(r'{.*}', '', data)


def lxml_eliminate_namespaces(target, nsmap):
    """
    Eliminate all namespaces from XML DOM.
    """
    for nsname, namespace in nsmap.items():
        lxml_remove_namespace(target, namespace)
        del target.nsmap[nsname]
    target.nsmap.clear()
    objectify.deannotate(target, xsi_nil=True, cleanup_namespaces=True)
    return target


def lxml_remove_namespace(doc, namespace):
    """
    Remove namespace in the obtained document in-place.
    """
    ns = "{%s}" % namespace
    nsl = len(ns)
    for elem in doc.getiterator():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]


def purge_dict_keys(data, prefix: str):
    """
    Purge all items whose keys start with `@xmlns`.
    """
    for key, value in data.copy().items():
        if key.startswith(prefix):
            del data[key]
        if isinstance(value, dict):
            data[key] = purge_dict_keys(value, prefix)
    return data
