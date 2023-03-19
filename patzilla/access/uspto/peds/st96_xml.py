# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Access the USPTO PEDS archive files in WIPO ST.96 XML format.

https://ped.uspto.gov/
"""
import dataclasses
import logging
import typing as t
from collections import OrderedDict
from copy import copy
from datetime import datetime
from pathlib import Path

import click
import jsonpointer
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from patzilla.access.uspto.peds.model import (
    ResultDictType,
    TransactionItem,
    UsptoPedsTransactionEvent,
    UsptoPedsTransactionEventType,
    resolve_transaction_codes,
)
from patzilla.boot.logging import setup_logging
from patzilla.util.config import to_list
from patzilla.util.data.processor import AbstractProcessorHandler, Processor
from patzilla.util.xml.reader import GenericXmlReader, XmlNodeDefinition, XmlNodeType

logger = logging.getLogger(__name__)


class Pointer:
    """
    Metadata for extracting data from nested data structure.
    """
    organization_name = jsonpointer.JsonPointer("/PublicationContact/Name/OrganizationName/OrganizationStandardName")
    person_structured_name = jsonpointer.JsonPointer("/PublicationContact/Name/PersonName/PersonStructuredName")
    entity_name = jsonpointer.JsonPointer("/Contact/Name/EntityName")
    correspondent_name = jsonpointer.JsonPointer("/Contact/Name/PersonName/PersonStructuredName")


class XmlRequest:
    """
    A request to the XML data.
    """

    def __init__(self, attributes: t.List[str] = None, transaction_codes: t.List[UsptoPedsTransactionEventType] = None):
        self.attributes = attributes or []
        self.transaction_codes = transaction_codes or []


class XmlReader(GenericXmlReader):
    """
    Read USPTO PEDS archive files in WIPO ST.96 XML format.

    Example files:

    - https://ped.uspto.gov/api/full-download?fileName=2020-2022-pairbulk-full-20221106-xml
    """

    ATTRIBUTES = {
        "app_type": XmlNodeDefinition(
            tag="uspat:PatentCaseMetadata/uscom:ApplicationTypeCategory", type=XmlNodeType.TEXT
        ),
        "app_status": XmlNodeDefinition(
            tag="uspat:PatentCaseMetadata/uscom:ApplicationStatusCategory", type=XmlNodeType.TEXT
        ),
        "app_status_date": XmlNodeDefinition(
            tag="uspat:PatentCaseMetadata/uscom:ApplicationStatusDate", type=XmlNodeType.TEXT
        ),
        "appl_id": XmlNodeDefinition(tag="uspat:PatentCaseMetadata/uscom:ApplicationNumberText", type=XmlNodeType.TEXT),
        "app_entity_status": XmlNodeDefinition(
            tag="uspat:PatentCaseMetadata/uscom:BusinessEntityStatusCategory", type=XmlNodeType.TEXT
        ),
        # "patent_title": XmlNodeDefinition(tag="uspat:PatentCaseMetadata/pat:InventionTitle", type=XmlNodeType.TEXT),
        "patent_number": XmlNodeDefinition(
            tag="uspat:PatentCaseMetadata/uspat:PatentGrantIdentification/pat:PatentNumber", type=XmlNodeType.TEXT
        ),
        "patent_issue_date": XmlNodeDefinition(
            tag="uspat:PatentCaseMetadata/uspat:PatentGrantIdentification/pat:GrantDate", type=XmlNodeType.TEXT
        ),
        "applicants": XmlNodeDefinition(
            tag="uspat:PatentCaseMetadata/uspat:PartyBag/pat:ApplicantBag/pat:Applicant/", type=XmlNodeType.VERBATIM
        ),
        "assignees": XmlNodeDefinition(
            tag="uspat:AssignmentDataBag/uspat:AssignmentData/pat:AssigneeBag/pat:Assignee/", type=XmlNodeType.VERBATIM
        ),
        "transactions": XmlNodeDefinition(
            tag="uspat:ProsecutionHistoryDataBag/uspat:ProsecutionHistoryData", type=XmlNodeType.VERBATIM
        ),
        # "assignments": XmlNodeDefinition(tag="uspat:AssignmentDataBag", type=XmlNodeType.VERBATIM),
        # "inventors": XmlNodeDefinition(
        #    tag="uspat:PatentCaseMetadata/uspat:PartyBag/pat:InventorBag/pat:Inventor/", type=XmlNodeType.VERBATIM
        # ),
        # "party_correspondents": XmlNodeDefinition(
        #    tag="uspat:PatentCaseMetadata/uspat:PartyBag/com:CorrespondenceAddress/com:Contact",
        #    type=XmlNodeType.VERBATIM,
        # ),
        # "assignment_correspondents": XmlNodeDefinition(
        #    tag="uspat:AssignmentDataBag/uspat:AssignmentData/com:CorrespondenceAddress", type=XmlNodeType.VERBATIM
        # ),
    }

    def __init__(self, resource: str, request: XmlRequest):
        super().__init__(resource=resource)
        self.request = request

    def read(self):
        """
        Read WIPO ST.96 XML from file, filter, and return records as nested dictionaries,
        converted from XML using `xmltodict`.
        """
        data = tqdm(self.read_st96_xml())

        # output = to_json(filtered)
        # return data

        data = self.filter_by_status(data)
        data = self.to_dict(data)
        data = self.decode(data)
        data = self.finalize(data)
        data = self.project(data)
        return data

    def read_st96_xml(self):
        """
        Read `<uspat:PatentData>` elements from input.
        """
        logger.info(f"Reading WIPO ST.96 XML from {self.resource}")
        return self.read_xml(tag="{urn:us:gov:doc:uspto:patent}PatentData")

    def filter_by_status(self, data):
        """
        Filter elements.
        """
        FOCUS = "29792448"

        for element in data:

            # This is a debugging mechanism. It skips all other documents than the one in FOCUS.
            # appl_id = self._get_xml_field(element, "appl_id")
            # print("appl_id:", appl_id)
            # 17567689
            # if appl_id != "17567714":  # 17625749, 17636910, 17854164
            # if appl_id != FOCUS:
            #    continue
            # print("YEAH")

            app_status = self._get_xml_field(element, "app_status")
            app_entity_status = self._get_xml_field(element, "app_entity_status")

            # FIXME: Don't hard-code the constraints.
            if app_status == "Patented Case" and app_entity_status != "UNDISCOUNTED":
                yield element

    def decode(self, data):
        """
        Forward decoding of document details to `XmlDecoder`.
        """
        for document in data:
            yield XmlDecoder(data=document, transaction_codes=self.request.transaction_codes).decode()

    def finalize(self, data):
        """
        Apply custom refinements to the output data.

        1. Display transactions in chronological order.
        2. Optionally fill `applicants` with data from `assignees`.
        """
        for document in data:

            # Reverse list of transactions, to be in chronological order.
            if document["transactions"]:
                document["transactions"] = list(reversed(document["transactions"]))

            # Use the last `assignee`, if the `applicants` field is empty.
            if not document["applicants"] and document["assignees"]:
                document["applicants"] = [document["assignees"][-1]]

            yield document

    def project(self, data):
        """
        Uses `self.attributes` to project corresponding attributes from `USApplication` instance.
        """

        output: ResultDictType = OrderedDict()
        for document in data:
            if self.request.attributes:
                for attribute in self.request.attributes:
                    output[attribute] = document.get(attribute)
            else:
                output = document

            yield output

    def to_csv(self, data):
        """
        Generate CSV output from input data.

        Please note it is a highly customized implementation which extracts and serializes
        allowance-notification-, and issue-notification-dates in a special way.
        """
        separator = ","

        def mkline(record):
            return separator.join(record)

        fields_wo_transactions = copy(self.request.attributes)[:-1]
        csv_headers = fields_wo_transactions + [
            "allowance_notification_1_date",
            "allowance_notification_2_date",
            "issue_notification_1_date",
            "issue_notification_2_date",
        ]
        yield mkline(csv_headers)

        for document in data:

            parts = []
            for key, value in document.items():
                # Serializing `transactions` MUST yield four columns, in the designated order.
                # Two for allowance-notification-, and another two for issue-notification-dates.
                if key == "transactions":
                    events_allowance = []
                    events_issue = []

                    # FIXME: Obtain constraints from `XmlRequest` instance.
                    for elem in value:
                        if elem["code"] == UsptoPedsTransactionEvent.ALLOWANCE_NOTICE_MAILED.value.code:
                            events_allowance.append(elem["date"])
                        if elem["code"] == UsptoPedsTransactionEvent.ISSUANCE_NOTIFICATION_MAILED.value.code:
                            events_issue.append(elem["date"])

                    if len(events_allowance) < 2:
                        events_allowance += [None]
                    if len(events_issue) < 2:
                        events_issue += [None]

                    for item in events_allowance + events_issue:
                        if item:
                            parts.append(f'"{str(item)}"')
                        else:
                            parts.append("")
                    continue
                if value is None:
                    value = ""
                elif isinstance(value, str):
                    pass
                elif isinstance(value, list):
                    value = "; ".join(value)
                elif isinstance(value, datetime.date):
                    value = str(value)
                else:
                    raise ValueError(f"Unable to encode type={type(value)}, value={value}")
                if value:
                    value = f'"{value}"'
                parts.append(value)

            yield mkline(parts)


class XmlDecoder:
    """
    Decode a single record in ST.96 XML format.
    """

    def __init__(self, data: t.Union[t.Dict, t.List], transaction_codes=None):
        self.data = data
        self.transaction_codes = transaction_codes

    def decode(self):
        self.data["applicants"] = self.decode_name_members(slot="applicants")
        self.data["inventors"] = self.decode_name_members(slot="inventors")
        self.data["assignees"] = self.decode_name_members(slot="assignees")
        # self.decode_party_correspondents()
        # self.decode_assignment_correspondents()
        self.data["transactions"] = self.decode_transactions()
        return self.data

    def decode_name_members(self, slot):
        """
        Attempt three different kinds of resolving entity, organization, or person names.
        """
        values = []
        if slot in self.data:
            nodes = to_list(self.data[slot])
            for item in nodes:
                try:
                    entity_name = Pointer.entity_name.resolve(item)
                    if entity_name:
                        values.append(entity_name)
                except jsonpointer.JsonPointerException:
                    try:
                        organization_name = Pointer.organization_name.resolve(item)
                        if organization_name:
                            values.append(organization_name)
                    except jsonpointer.JsonPointerException:
                        try:
                            person_name = self.decode_person_name(Pointer.person_structured_name.resolve(item))
                            if person_name:
                                values.append(person_name)
                        except jsonpointer.JsonPointerException:
                            pass
            return values

    def decode_party_correspondents(self):
        values = []
        if "party_correspondents" in self.data:
            nodes = to_list(self.data["party_correspondents"])
            for item in nodes:
                try:
                    correspondent_name = self.decode_person_name(Pointer.correspondent_name.resolve(item))
                    if correspondent_name:
                        values.append(correspondent_name)
                except:
                    pass
            return values

    def decode_assignment_correspondents(self):
        values = []
        if "assignment_correspondents" in self.data:
            nodes = to_list(self.data["assignment_correspondents"][0]["CorrespondenceAddress"])
            for item in nodes:
                try:
                    entity_name = Pointer.entity_name.resolve(item)
                    if entity_name:
                        values.append(entity_name)
                except:
                    correspondent_name = self.decode_person_name(Pointer.correspondent_name.resolve(item))
                    if correspondent_name:
                        values.append(correspondent_name)
            return values

    def decode_person_name(self, node: t.Dict):
        """
        Decode a `PersonStructuredName` of this form.

        <com:PersonStructuredName>
            <com:FirstName>Kirk</com:FirstName>
            <com:MiddleName></com:MiddleName>
            <com:LastName>Damman</com:LastName>
            <com:NameSuffix></com:NameSuffix>
        </com:PersonStructuredName>
        """
        if node is None:
            return
        person_name_fields = ["FirstName", "MiddleName", "LastName"]
        person_name_parts = []
        for field in person_name_fields:
            if field in node and node[field]:
                person_name_parts.append(node[field])
        name = " ".join(person_name_parts)
        return name

    def decode_transactions(self):
        """
        Decode list of transaction event items, with optional filtering.
        """

        # Prepare list of wanted codes.
        codes_real: t.List[UsptoPedsTransactionEvent] = resolve_transaction_codes(codes=self.transaction_codes)

        values = []
        if "transactions" in self.data:
            for item in self.data["transactions"]:
                transaction = TransactionItem(
                    code=item["ProsecutionHistoryData"]["EventCode"],
                    date=item["ProsecutionHistoryData"]["EventDate"],
                    description=item["ProsecutionHistoryData"]["EventDescriptionText"],
                )
                if not codes_real or transaction.code in codes_real:
                    values.append(dataclasses.asdict(transaction))
            return values


class CompactCsvConverter(AbstractProcessorHandler):
    """
    Convert ST.96 `uspat:PatentData` records to compact CSV representation.
    """

    @property
    def suffix(self):
        return ".csv"

    def handle(self, resource, outstream: t.IO[str]):
        """
        Convert single ST.96 XML document from file or stream to CSV format.
        """

        request = XmlRequest(
            # Select requested attributes.
            attributes=[
                "app_type",
                "appl_id",
                # "app_filing_date",
                "app_entity_status",
                # "app_early_pub_number",
                # "app_early_pub_date",
                # "app_status",
                # "app_status_date",
                "patent_number",
                "patent_issue_date",
                # "patent_title",
                "applicants",
                # "inventors",
                # "assignees",
                # "correspondents",
                "transactions",
            ],
            # Select requested transaction event types.
            transaction_codes=[
                # UsptoPedsTransactionEvent.ALLOWANCE_NOTICE_VERIFICATION_COMPLETED,
                UsptoPedsTransactionEvent.ALLOWANCE_NOTICE_MAILED,
                # UsptoPedsTransactionEvent.ISSUANCE_CONSIDERED_READY,
                UsptoPedsTransactionEvent.ISSUANCE_NOTIFICATION_MAILED,
            ],
        )
        reader = XmlReader(resource=resource, request=request)

        with logging_redirect_tqdm():

            # JSON
            # for record in reader.read():
            #    print(json.dumps(record))

            # CSV
            for record in reader.to_csv(reader.read()):
                outstream.write(record)
                outstream.write("\n")


@click.command(name="process")
@click.option("--resource", type=str, required=True)
@click.option("--outdir", envvar="PATZILLA_OUTDIR", type=Path, required=False)
@click.option("--format", "output_format", type=click.Choice(["csv-compact"]), default="csv-compact", required=True)
def process_cli(resource: str, outdir: Path, output_format: str):

    # Sanity checks.
    if output_format == "csv-compact":
        handler = CompactCsvConverter()
    else:
        raise KeyError(f"Output format '{output_format}' is not supported")

    # Invoke processing pipeline.
    logger.info(f"Input file:  {resource}")

    # Process one or multiple ST.96 XML documents from XML or ZIP files.
    processor = Processor(handler=handler, outdir=outdir, outprefix="uspto-peds-compact_")
    processor.process(resource)

    logger.info("Ready.")


if __name__ == "__main__":
    """
    Acquire data::
    
        alias fetch='aria2c --max-connection-per-server=8 --split=8 --continue=true'
        fetch "https://ped.uspto.gov/api/full-download?fileName=2000-2019-pairbulk-full-20221204-xml"
        fetch "https://ped.uspto.gov/api/full-download?fileName=2020-2022-pairbulk-full-20221204-xml"
        
    Run program::

        # Process single ST.96 XML file.
        python -m patzilla.access.uspto.peds.st96_xml \
            --resource /path/to/16629552.st96.xml

        # Process PAIRBULK XML file for particular year.
        python -m patzilla.access.uspto.peds.st96_xml \
            --resource /path/to/2020-2022-pairbulk-full-20221113-xml/2020.xml \
            --outdir tmp/peds-output

        # Process all XML files in PAIRBULK zip archive file.
        export PATZILLA_OUTDIR=tmp/peds-output
        python -m patzilla.access.uspto.peds.st96_xml \
            --resource /path/to/2020-2022-pairbulk-full-20221113-xml.zip

    Todo:

    - Skip over existing output files, unless `--overwrite` is given.
    - Option for including or excluding files per name pattern, also within archive files.
      For example, when reading files from `2000-2019-pairbulk-full-xml.zip`, process only years 2010-.
    """
    setup_logging()
    process_cli()
