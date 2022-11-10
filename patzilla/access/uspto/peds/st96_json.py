# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Access the USPTO PEDS archive files in WIPO ST.96 JSON format.

https://ped.uspto.gov/
"""
import dataclasses
import datetime
import functools
import json
import logging
import typing as t
from collections import OrderedDict
from copy import copy
from enum import Enum

import json_stream
import jsonpointer
from json_stream.base import PersistentStreamingJSONObject
from patent_client import USApplication
from patent_client.util.json_encoder import JsonEncoder
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

logger = logging.getLogger(__name__)


class UsptoPedsAppStatus(Enum):
    PATENTED = "Patented Case"
    EXPIRED_NONPAYMENT = "Patent Expired Due to NonPayment of Maintenance Fees Under 37 CFR 1.362"
    PROVISIONAL_APPLICATION_EXPIRED = "Provisional Application Expired"
    ABANDONED_OFFICE_ACTION = "Abandoned -- Failure to Respond to an Office Action"
    ABANDONED_ISSUE_FEE = "Abandoned -- Failure to Pay Issue Fee"
    ABANDONED_EXAMINER = "Abandoned -- After Examiner's Answer or Board of Appeals Decision"
    DOCKETED_NEW_CASE = "Docketed New Case - Ready for Examination"
    RO_PROCESSING_COMPLETED = "RO PROCESSING COMPLETED-PLACED IN STORAGE"


def parse_date(value):
    return datetime.datetime.strptime(value, "%Y-%m-%d").date()


class Pointer:
    app_type = jsonpointer.JsonPointer("/patentCaseMetadata/applicationTypeCategory")
    app_number = jsonpointer.JsonPointer("/patentCaseMetadata/applicationNumberText/value")
    app_filing_date = jsonpointer.JsonPointer("/patentCaseMetadata/filingDate")

    app_status = jsonpointer.JsonPointer("/patentCaseMetadata/applicationStatusCategory")
    app_status_date = jsonpointer.JsonPointer("/patentCaseMetadata/applicationStatusDate")

    invention_title = jsonpointer.JsonPointer("/patentCaseMetadata/inventionTitle/content")
    publication_number = jsonpointer.JsonPointer(
        "/patentCaseMetadata/patentPublicationIdentification/publicationNumber"
    )
    publication_date = jsonpointer.JsonPointer("/patentCaseMetadata/patentPublicationIdentification/publicationDate")
    patent_number = jsonpointer.JsonPointer("/patentCaseMetadata/patentGrantIdentification/patentNumber")
    patent_date = jsonpointer.JsonPointer("/patentCaseMetadata/patentGrantIdentification/grantDate")

    applicant_inventor_bag = jsonpointer.JsonPointer("/patentCaseMetadata/partyBag/applicantBagOrInventorBagOrOwnerBag")

    business_entity_status = jsonpointer.JsonPointer("/patentCaseMetadata/businessEntityStatusCategory")
    prosecution_history = jsonpointer.JsonPointer("/prosecutionHistoryDataBag/prosecutionHistoryData")


@dataclasses.dataclass
class JsonDocument:
    data: t.Dict
    usdoc: USApplication = None
    projected: t.Optional[ResultDictType] = None

    def to_json(self):
        # return json.dumps(self.data, cls=JSONStreamEncoder)
        return json.dumps(self.projected, cls=JsonEncoder)

    def to_dict(self):
        return self.usdoc.to_dict()

    def to_csv(self, separator=","):
        parts = []
        for key, value in self.projected.items():
            # FIXME: Improve transaction decoding.
            #        Currently, it will, for example, break on `"appl_id": "17571430"`, because this document
            #        has multiple `"code": "MN/=."` transaction event items. Thus, the new code MUST NOT rely
            #        on the order of those items.
            if key == "transactions":
                for elem in value:
                    parts.append(str(elem["date"]))
                continue
            if value is None:
                value = ""
            elif isinstance(value, str):
                value = f'"{value}"'
            elif isinstance(value, list):
                value = f'"{separator.join(value)}"'
            elif isinstance(value, datetime.date):
                value = str(value)
            else:
                raise ValueError(f"Unable to encode type={type(value)}, value={value}")
            parts.append(value)
        return separator.join(parts)


class JsonRequest:
    """
    A request to the JSON data.
    """

    def __init__(self, attributes: t.List[str] = None, transaction_codes: t.List[UsptoPedsTransactionEventType] = None):
        self.attributes = attributes or []
        self.transaction_codes = transaction_codes or []

    def filter(self, items: t.Iterable[JsonDocument]) -> t.Generator[JsonDocument, None, None]:
        """
        Filter elements.

        FIXME: Don't hard-code the constraints.
        """
        for jdoc in items:
            try:
                jdoc.usdoc.app_status = Pointer.app_status.resolve(jdoc.data)
                jdoc.usdoc.app_status_date = parse_date(Pointer.app_status_date.resolve(jdoc.data))
                jdoc.usdoc.app_entity_status = Pointer.business_entity_status.resolve(jdoc.data)
                if jdoc.usdoc.app_status == "Patented Case" and jdoc.usdoc.app_entity_status != "UNDISCOUNTED":
                    yield jdoc
            except jsonpointer.JsonPointerException:
                logger.warning(f"Document appl_id={jdoc.usdoc.appl_id} lacks {Pointer.app_status.path}")

    def decode(self, items: t.Iterable[JsonDocument]) -> t.Generator[JsonDocument, None, None]:

        for jdoc in items:

            # Decode patent title.
            jdoc.usdoc.patent_title = Pointer.invention_title.resolve(jdoc.data)

            # Decode publication and patent number and dates.
            """
            "patentPublicationIdentification":{"publicationNumber":"US20220273742A1","publicationDate":"2022-09-01"}
            "patentGrantIdentification":{"patentNumber":"D959194","grantDate":"2022-08-02"}
            """
            try:
                jdoc.usdoc.app_early_pub_number = Pointer.publication_number.resolve(jdoc.data)
                jdoc.usdoc.app_early_pub_date = parse_date(Pointer.publication_date.resolve(jdoc.data))
            except jsonpointer.JsonPointerException:
                logger.warning(f"Document appl_id={jdoc.usdoc.appl_id} lacks {Pointer.publication_number.path}")
            try:
                jdoc.usdoc.patent_number = Pointer.patent_number.resolve(jdoc.data)
                jdoc.usdoc.patent_issue_date = parse_date(Pointer.patent_date.resolve(jdoc.data))
            except jsonpointer.JsonPointerException:
                logger.warning(f"Document appl_id={jdoc.usdoc.appl_id} lacks {Pointer.patent_number.path}")

            # Decode applicants.
            applicant_inventor_bag = Pointer.applicant_inventor_bag.resolve(jdoc.data)
            applicants = []
            try:
                applicant_list = self._find_node(applicant_inventor_bag, "applicant", [])
                for applicant_item in applicant_list:
                    try:
                        applicant_name_container = applicant_item["contactOrPublicationContact"][0]
                        applicant_name = self._parse_name(applicant_name_container)
                        if applicant_name:
                            applicants.append(applicant_name)
                    except (IndexError, KeyError) as ex:
                        logger.warning(
                            f"Decoding applicants failed. appl_id={jdoc.usdoc.appl_id} Reason: {ex.__class__.__name__}({ex})"
                        )
            except Exception as ex:
                logger.warning(
                    f"Decoding applicants failed. appl_id={jdoc.usdoc.appl_id} Reason: {ex.__class__.__name__}({ex})"
                )
                raise
            jdoc.usdoc.applicants = applicants

            # Decode party identifier and contact information.
            party_identifier_contacts = self._find_node(applicant_inventor_bag, "partyIdentifierOrContact", [])
            contacts = []
            for contact_item in party_identifier_contacts:
                try:
                    name = self._parse_name(contact_item)
                    if name:
                        contacts.append(name)
                except Exception as ex:
                    logger.warning(
                        f"Decoding contacts failed. appl_id={jdoc.usdoc.appl_id} Reason: {ex.__class__.__name__}({ex})"
                    )
            jdoc.usdoc.correspondent = contacts

            # Decode transactions.
            jdoc.usdoc.transactions = self._get_transactions(jdoc)

            yield jdoc

    def _find_node(self, container, key, default=None):
        for item in container:
            if key in item:
                return item[key]
        return default

    def _parse_name(self, node: t.Dict):
        if "name" not in node:
            return
        person_or_organization = node["name"]["personNameOrOrganizationNameOrEntityName"][0]
        if "organizationStandardName" in person_or_organization:
            name = person_or_organization["organizationStandardName"]["content"][0]
        elif "personStructuredName" in person_or_organization:
            person_structured_name = person_or_organization["personStructuredName"]
            person_name_fields = ["firstName", "middleName", "lastName"]
            person_name_parts = []
            for field in person_name_fields:
                if field in person_structured_name and person_structured_name[field]:
                    person_name_parts.append(person_structured_name[field])
            name = " ".join(person_name_parts)
        else:
            raise KeyError(
                f"Unable to parse `name` information from node {node}, "
                f"neither `organizationStandardName` nor `personStructuredName` found"
            )
        return name

    def _get_transactions(self, jdoc: JsonDocument) -> t.Generator[t.Dict, None, None]:

        # Prepare list of events codes.
        codes_real: t.List[UsptoPedsTransactionEvent] = resolve_transaction_codes(codes=self.transaction_codes)

        # Filter list of transactions.
        try:
            prosecution_history = Pointer.prosecution_history.resolve(jdoc.data)
        except jsonpointer.JsonPointerException:
            logger.warning(f"Document appl_id={jdoc.usdoc.appl_id} lacks {Pointer.prosecution_history.path}")
            return

        # TODO: Make `reversed` configurable?
        for item in reversed(prosecution_history):
            transaction = TransactionItem(
                date=parse_date(item["eventDate"]),
                code=item["eventCode"],
                description=item["eventDescriptionText"],
            )
            if not codes_real or transaction.code in codes_real:
                yield dataclasses.asdict(transaction)

    def project(self, items: t.Iterable[JsonDocument]) -> t.Generator[JsonDocument, None, None]:
        """
        Uses `self.attributes` to project corresponding attributes from `USApplication` instance.
        """

        for jdoc in items:
            data = jdoc.to_dict()
            output: ResultDictType = OrderedDict()
            if self.attributes:
                for attribute in self.attributes:
                    output[attribute] = data.get(attribute)
            else:
                output = data

            jdoc.projected = output
            yield jdoc


def compose(*funcs):
    return lambda x: functools.reduce(lambda f, g: g(f), list(funcs), x)


class JsonReader:
    """
    Read USPTO PEDS archive files in WIPO ST.96 JSON format.

    Example files:

    - https://ped.uspto.gov/api/full-download?fileName=1980-1999-pairbulk-full-20221106-json (2.7 GB)
    - https://ped.uspto.gov/api/full-download?fileName=2000-2019-pairbulk-full-20221106-json (30.6 GB)
    - https://ped.uspto.gov/api/full-download?fileName=2020-2022-pairbulk-full-20221106-json (2.6 GB)

    2020-2022-pairbulk-full-20221106-json.zip contains three files:

    - 2020.json (17G)
    - 2021.json (9.9G)
    - 2022.json (1.5G)
    """

    def __init__(self, filepath: str, request: JsonRequest):
        self.filepath = filepath
        self.request = request
        self.nsmap: t.Optional[t.Dict] = None

        # Debugging mechanism to skip all other documents than the one listed.
        self.skip_until_document = None
        # self.skip_until_document = "11303320"
        self.skip = bool(self.skip_until_document)

    def read(self, *elements) -> t.Generator[JsonDocument, None, None]:
        pipeline = compose(
            self.request.filter,
            self.request.decode,
            self.request.project,
            *elements,
        )
        return pipeline(self.read_st96_json())

    def read_st96_json(self) -> t.Generator[JsonDocument, None, None]:
        logger.info(f"Reading WIPO ST.96 JSON from {self.filepath}")
        f = open(self.filepath, "r")
        data = json_stream.load(f)

        item: PersistentStreamingJSONObject
        for item in tqdm(data["PatentBulkData"].persistent()):
            app_number = Pointer.app_number.resolve(item)
            if app_number == self.skip_until_document:
                self.skip = False
            if self.skip:
                logger.info(f"Skipping document {app_number}")
                continue
                # pass

            item.read_all()
            try:
                app_type = Pointer.app_type.resolve(item)
            except jsonpointer.JsonPointerException:
                app_type = None
            app_filing_date = parse_date(Pointer.app_filing_date.resolve(item))
            usapp = USApplication(appl_id=app_number, app_type=app_type, app_filing_date=app_filing_date)
            yield JsonDocument(data=item, usdoc=usapp)

    def to_dict(self, docs):
        for jdoc in docs:
            yield json.loads(jdoc.to_json())

    def to_csv(self, data):
        """
        Generate CSV output from input data.

        Please note it is a heavily customized implementation which extracts and serializes
        allowance-notification-, and issue-notification-dates in a special way.
        """

        separator = ","

        def mkline(record):
            return separator.join(record)

        csv_headers = copy(self.request.attributes)[:-1] + ["allowance_notification_date", "issue_notification_date"]
        yield mkline(csv_headers)

        for document in data:
            yield document.to_csv()


def main():
    # Read WIPO ST.96 JSON from file, filter, and return records as nested dictionaries.

    # WIPO ST.96 JSON files.
    resource = "/Users/amo/Downloads/2020-2022-pairbulk-full-20221106-json/2020.json"
    # resource = "/Users/amo/Downloads/2020-2022-pairbulk-full-20221106-json/2021.json"
    # resource = "/Users/amo/Downloads/2020-2022-pairbulk-full-20221106-json/2022.json"

    request = JsonRequest(
        # Select requested attributes.
        attributes=[
            "app_type",
            "appl_id",
            "app_filing_date",
            "app_entity_status",
            "app_early_pub_number",
            "app_early_pub_date",
            "app_status",
            "app_status_date",
            "patent_number",
            "patent_issue_date",
            "patent_title",
            "applicants",
            "correspondent",
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
    reader = JsonReader(filepath=resource, request=request)

    # CSV
    # separator = ","
    # csv_headers = copy(request.attributes)[:-1] + ["allowance_notification_date", "issue_notification_date"]
    # print(separator.join(map(lambda x: f'"{x}"', csv_headers)))

    with logging_redirect_tqdm():

        # JSON
        for document in reader.read():
            print(document.to_json())

        # CSV
        # for record in reader.to_csv(reader.read()):
        #    print(record)


if __name__ == "__main__":
    """
    Synopsis::

        python -m patzilla.access.uspto.peds.st96_json
    """
    setup_logging()
    main()
