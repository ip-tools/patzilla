# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Access the USPTO PEDS archive files in WIPO ST.96 JSON format.

https://ped.uspto.gov/
"""
import dataclasses
import datetime
import json
import logging
import typing as t
from enum import Enum

import json_stream
import jsonpointer
from json_stream.dump import JSONStreamEncoder
from patent_client import USApplication
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

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
    return datetime.datetime.strptime(value, "%Y-%m-%d")


@dataclasses.dataclass
class JsonDocument:
    data: t.Dict
    usdoc: t.Optional[USApplication] = None

    def to_json(self):
        return json.dumps(self.data, cls=JSONStreamEncoder)

    def to_dict(self):
        data = dict(self.__dict__)
        del data["data"]
        return data


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

    def __init__(self, filepath):
        self.filepath = filepath
        self.nsmap = None

    def read(self):
        """
        Read WIPO ST.96 JSON from file, filter, and return records as nested dictionaries.
        """
        data: t.Iterable[JsonDocument] = tqdm(self.read_st96_json())
        filtered = self.filter_by_status(data)
        output = self.project(filtered)
        # return self.to_dict(filtered)
        return output

    def read_st96_json(self) -> t.Generator[JsonDocument, None, None]:
        logger.info(f"Reading WIPO ST.96 JSON from {self.filepath}")
        f = open(self.filepath, "r")
        data = json_stream.load(f)

        for item in data["PatentBulkData"].persistent():
            app_number_pointer = jsonpointer.JsonPointer("/patentCaseMetadata/applicationNumberText/value")
            app_filing_date_pointer = jsonpointer.JsonPointer("/patentCaseMetadata/filingDate")
            jdoc = JsonDocument(data=item, usdoc=USApplication(appl_id=app_number_pointer.resolve(item)))
            jdoc.usdoc.app_filing_date = parse_date(app_filing_date_pointer.resolve(jdoc.data))
            yield jdoc

    def filter_by_status(self, data) -> t.Generator[JsonDocument, None, None]:
        """
        Filter elements.

        FIXME: Don't hard-code the constraints.
        """
        app_status_pointer = jsonpointer.JsonPointer("/patentCaseMetadata/applicationStatusCategory")
        app_status_date_pointer = jsonpointer.JsonPointer("/patentCaseMetadata/applicationStatusDate")
        for jdoc in data:
            try:
                jdoc.usdoc.app_status = app_status_pointer.resolve(jdoc.data)
                jdoc.usdoc.app_status_date = parse_date(app_status_date_pointer.resolve(jdoc.data))
                if jdoc.usdoc.app_status == "Patented Case":
                    yield jdoc
            except jsonpointer.JsonPointerException:
                logger.warning(f"Document appl_id={jdoc.usdoc.appl_id} lacks {app_status_pointer.path}")

    def project(self, docs: t.Iterable[JsonDocument]):
        """
        "patentPublicationIdentification":{"publicationNumber":"US20220273742A1","publicationDate":"2022-09-01"}
        "patentGrantIdentification":{"patentNumber":"D959194","grantDate":"2022-08-02"}
        """
        publication_number_pointer = jsonpointer.JsonPointer(
            "/patentCaseMetadata/patentPublicationIdentification/publicationNumber"
        )
        publication_date_pointer = jsonpointer.JsonPointer(
            "/patentCaseMetadata/patentPublicationIdentification/publicationDate"
        )
        patent_number_pointer = jsonpointer.JsonPointer("/patentCaseMetadata/patentGrantIdentification/patentNumber")
        patent_date_pointer = jsonpointer.JsonPointer("/patentCaseMetadata/patentGrantIdentification/grantDate")
        for jdoc in docs:
            try:
                jdoc.usdoc.app_early_pub_number = publication_number_pointer.resolve(jdoc.data)
                jdoc.usdoc.app_early_pub_date = parse_date(publication_date_pointer.resolve(jdoc.data))
            except jsonpointer.JsonPointerException:
                logger.warning(f"Document appl_id={jdoc.usdoc.appl_id} lacks {publication_number_pointer.path}")
            try:
                jdoc.usdoc.patent_number = patent_number_pointer.resolve(jdoc.data)
                jdoc.usdoc.patent_issue_date = parse_date(patent_date_pointer.resolve(jdoc.data))
            except jsonpointer.JsonPointerException:
                logger.warning(f"Document appl_id={jdoc.usdoc.appl_id} lacks {patent_number_pointer.path}")
            yield jdoc

    def to_dict(self, docs):
        for jdoc in docs:
            yield json.loads(jdoc.to_json())


def main():

    # WIPO ST.96 JSON files.
    resource = "/Users/amo/Downloads/2020-2022-pairbulk-full-20221106-json/2020.json"
    # resource = "/Users/amo/Downloads/2020-2022-pairbulk-full-20221106-json/2021.json"
    resource = "/Users/amo/Downloads/2020-2022-pairbulk-full-20221106-json/2022.json"

    reader = JsonReader(filepath=resource)
    with logging_redirect_tqdm():
        for record in reader.read():
            logger.info(f"Found document: patent_number={record.usdoc.patent_number}, status={record.usdoc.app_status}")
            print(record.usdoc.to_json())


if __name__ == "__main__":
    """
    Synopsis::

        python -m patzilla.access.uspto.peds.st96_json | jq
    """
    setup_logging()
    main()
