# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Access the USPTO PEDS archive files in ST.96 XML format.

https://ped.uspto.gov/
"""
import dataclasses
import json
import re
from collections import OrderedDict
from enum import Enum

import xmltodict
from lxml.etree import iterparse, tounicode
from tqdm import tqdm

from patzilla.util.xml.format import (
    BadgerFishNoNamespace,
    lxml_eliminate_namespaces,
    purge_dict_keys,
)


class XmlNodeType(Enum):
    TEXT = 1
    DICT = 2
    VERBATIM = 3


@dataclasses.dataclass
class XmlNodeDefinition:
    tag: str
    type: XmlNodeType


class XmlDeserializerType(Enum):
    XMLTODICT = 1
    BADGERFISH = 2


class XmlReader:
    """
    Read USPTO PEDS archive files in XML format.

    Example files:

    - https://ped.uspto.gov/api/full-download?fileName=2020-2022-pairbulk-full-20221106-xml
    """

    ATTRIBUTES = {
        "app_status": XmlNodeDefinition(tag="*/uscom:ApplicationStatusCategory", type=XmlNodeType.TEXT),
        "patent_title": XmlNodeDefinition(tag="*/pat:InventionTitle", type=XmlNodeType.TEXT),
        "patent_grant": XmlNodeDefinition(tag="*/uspat:PatentGrantIdentification", type=XmlNodeType.DICT),
        "assignments": XmlNodeDefinition(tag="uspat:AssignmentDataBag", type=XmlNodeType.VERBATIM),
        "applicants": XmlNodeDefinition(tag="**/pat:ApplicantBag", type=XmlNodeType.VERBATIM),
    }

    DESERIALIZER = XmlDeserializerType.XMLTODICT

    def __init__(self, filepath):
        self.filepath = filepath
        self.nsmap = None

    def read(self):
        """
        Read ST.96 XML from file, filter, and return records as nested dictionaries,
        converted from XML using `xmltodict`.
        """
        data = self.read_st96_xml()
        filtered = self.filter_by_status(data)
        # output = to_json(filtered)
        return self.to_dict(filtered)

    def read_st96_xml(self):
        """
        Split `<uspat:PatentBulkData>` into `<uspat:PatentData>` elements.
        """
        f = open(self.filepath, mode="rb")
        iter_elems = iterparse(f, events=("start", "end"), resolve_entities=True)
        for event, element in iter_elems:
            if event == "start":

                # Memorize namespaces from root element.
                if self.nsmap is None:
                    self.nsmap = element.nsmap

                if element.tag == "{urn:us:gov:doc:uspto:patent}PatentData":
                    yield element

    def filter_by_status(self, data):
        """
        Filter elements.

        FIXME: Don't hard-code the constraints.
        """
        for element in data:
            tag = "*/uscom:ApplicationStatusCategory"
            res = element.find(tag, self.nsmap)
            if res is not None:
                if res.text == "Patented Case":
                    yield element

    def to_dict(self, data):
        """
        Convert XML DOM to nested data structor.
        """
        for element in data:
            output = {}
            for name, item in self.ATTRIBUTES.items():
                tag = item.tag
                pattern = tag
                target = element.find(pattern, self.nsmap)
                if target is not None:
                    if item.type == XmlNodeType.TEXT:
                        output[name] = target.text
                    elif item.type == XmlNodeType.DICT:
                        nested = OrderedDict()
                        for child in target.getchildren():
                            basetag = re.sub("^{.*}", "", child.tag)
                            nested[basetag] = child.text
                        output[name] = nested
                    elif item.type == XmlNodeType.VERBATIM:

                        if self.DESERIALIZER == XmlDeserializerType.XMLTODICT:
                            lxml_eliminate_namespaces(target, nsmap=self.nsmap)
                            data = xmltodict.parse(tounicode(target))
                            data = purge_dict_keys(data, prefix="@xmlns")

                        elif self.DESERIALIZER == XmlDeserializerType.BADGERFISH:
                            data = BadgerFishNoNamespace(xml_fromstring=False, dict_type=OrderedDict).data(target)

                        else:
                            raise KeyError(f"Unknown XML deserializer selected: {self.DESERIALIZER}")

                        output[name] = data
            yield output

    def to_json(self, data):
        """
        Convert XML DOM to JSON.
        """
        for element in data:
            xml = tounicode(element)
            # print(xml)
            yield json.dumps(xmltodict.parse(xml))


def main():
    reader = XmlReader(filepath="/Users/amo/Downloads/pairbulk-delta-20221107-xml/2022.xml")
    for record in tqdm(reader.read()):
        # print("=" * 42)
        print(json.dumps(record))


if __name__ == "__main__":
    """
    Synopsis::

        python -m patzilla.access.uspto.peds.rawdata | jq
    """
    main()
