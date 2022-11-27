# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import dataclasses
import json
import logging
import re
from collections import OrderedDict
from enum import Enum

import xmltodict
from lxml.etree import iterparse, tounicode

from patzilla.util.config import to_list
from patzilla.util.xml.format import BadgerFishNoNamespace, lxml_eliminate_namespaces, purge_dict_keys

logger = logging.getLogger(__name__)


class XmlDeserializerType(Enum):
    XMLTODICT = 1
    BADGERFISH = 2


class XmlNodeType(Enum):
    TEXT = 1
    DICT = 2
    VERBATIM = 3


@dataclasses.dataclass
class XmlNodeDefinition:
    tag: str
    type: XmlNodeType


class GenericXmlReader:

    ATTRIBUTES = {}
    DESERIALIZER = XmlDeserializerType.XMLTODICT

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.nsmap = None

    def read_xml(self, tag=None):
        """
        Incrementally parse XML file, emitting node 'end' events.
        When given a 'tag', it will only emit events for elements that match the given tag.
        """
        with open(self.filepath, mode="rb") as f:
            context = iterparse(f, tag=tag, events=("end",), resolve_entities=True)
            for event, element in fast_iter(context):

                # Memorize namespaces from root element.
                if self.nsmap is None:
                    self.nsmap = element.nsmap

                yield element

    def _get_xml_field(self, element, fieldname: str):
        """
        Extract a value from the XML DOM, using the tag from the `self.ATTRIBUTES` registry.
        """
        return self._find_text_by_tag(element, self.ATTRIBUTES[fieldname].tag)

    def _find_text_by_tag(self, element, tag: str):
        """
        Find XML DOM node by tag, and return text content.
        """
        res = element.find(tag, self.nsmap)
        if res is not None:
            return res.text

    def to_dict(self, data):
        """
        Unmarshal XML DOM to nested data structure, using `xmltodict` or BadgerFish.
        """
        for element in data:
            output = {}
            for name, item in self.ATTRIBUTES.items():
                tag = item.tag
                pattern = tag
                target = element.findall(pattern, self.nsmap)
                if target is None or not target:
                    # logger.warning(f"Tag {pattern} not found")
                    continue

                if item.type == XmlNodeType.TEXT:
                    output[name] = target[0].text

                elif item.type == XmlNodeType.DICT:
                    nested = OrderedDict()
                    for child in target.getchildren():
                        basetag = re.sub("^{.*}", "", child.tag)
                        nested[basetag] = child.text
                    output[name] = nested

                elif item.type == XmlNodeType.VERBATIM:
                    items = []
                    for el in to_list(target):
                        if self.DESERIALIZER == XmlDeserializerType.XMLTODICT:
                            lxml_eliminate_namespaces(el, nsmap=self.nsmap)
                            _data = xmltodict.parse(tounicode(el))
                            _data = purge_dict_keys(_data, prefix="@xmlns")
                            items.append(_data)

                        elif self.DESERIALIZER == XmlDeserializerType.BADGERFISH:
                            _data = BadgerFishNoNamespace(xml_fromstring=False, dict_type=OrderedDict).data(target)
                            items.append(_data)

                        else:
                            raise KeyError(f"Unknown XML deserializer selected: {self.DESERIALIZER}")

                    output[name] = items
            yield output

    def to_json(self, data):
        """
        Convert XML DOM to JSON.
        """
        for element in data:
            xml = tounicode(element)
            yield json.dumps(xmltodict.parse(xml))


def fast_iter(context):
    """
    https://lxml.de/parsing.html#modifying-the-tree

    Based on Liza Daly's `fast_iter`.
    https://web.archive.org/web/20210309115224/http://www.ibm.com/developerworks/xml/library/x-hiperfparse/

    See also https://web.archive.org/web/20200703234426/http://effbot.org/zone/element-iterparse.htm

    -- https://stackoverflow.com/a/12161078
    """
    for event, elem in context:
        yield event, elem
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath("ancestor-or-self::*"):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context
