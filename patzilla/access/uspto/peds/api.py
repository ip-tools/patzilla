# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Access the USPTO PEDS HTTP API.

https://ped.uspto.gov/
"""
import dataclasses
import datetime
import json
import logging
import typing as t
from collections import OrderedDict
from enum import Enum

import rfc3339
from patent_client import USApplication
from patent_client.uspto.peds.manager import USApplicationManager
from patent_client.util.json_encoder import JsonEncoder

from patzilla.boot.logging import setup_logging

logger = logging.getLogger(__name__)


class UsptoPedsAppStatus(Enum):
    PATENTED = '"Patented Case"'
    EXPIRED_NONPAYMENT = '"Patent Expired Due to NonPayment of Maintenance Fees Under 37 CFR 1.362"'
    PROVISIONAL_APPLICATION_EXPIRED = '"Provisional Application Expired"'
    ABANDONED_OFFICE_ACTION = "Abandoned*Failure?to?Respond?to?an?Office?Action"
    ABANDONED_ISSUE_FEE = "Abandoned*Failure?to?Pay?Issue?Fee"
    ABANDONED_EXAMINER = "Abandoned*After?Examiner's?Answer?or?Board?of?Appeals?Decision"
    DOCKETED_NEW_CASE = '"Docketed New Case - Ready for Examination"'
    RO_PROCESSING_COMPLETED = '"RO PROCESSING COMPLETED-PLACED IN STORAGE"'


@dataclasses.dataclass
class UsptoPedsTransactionEventDefinition:
    code: str
    description: str


class UsptoPedsTransactionEvent(Enum):
    """
    - code: N/=.
      Notice of Allowance Data Verification Completed

    - code: MN/=.
      Mail Notice of Allowance

    - code: PILS
      Application Is Considered Ready for Issue

    - code: WPIR
      Issue Notification Mailed

    """

    ALLOWANCE_NOTICE_VERIFICATION_COMPLETED = UsptoPedsTransactionEventDefinition(
        code="N/=.", description="Notice of Allowance Data Verification Completed"
    )
    ALLOWANCE_NOTICE_MAILED = UsptoPedsTransactionEventDefinition(code="MN/=.", description="Mail Notice of Allowance")
    ISSUANCE_CONSIDERED_READY = UsptoPedsTransactionEventDefinition(
        code="PILS", description="Application Is Considered Ready for Issue"
    )
    ISSUANCE_NOTIFICATION_MAILED = UsptoPedsTransactionEventDefinition(
        code="WPIR", description="Issue Notification Mailed"
    )

    def __eq__(self, other):
        return self.value == other or self.value.code == other


ResultDictType = t.OrderedDict[str, t.Union[str, t.List]]
TransactionDictType = t.Dict[str, str]
UsptoPedsTransactionEventType = t.Union[UsptoPedsTransactionEvent, str]


@dataclasses.dataclass
class UsptoPedsResponse:
    count: int
    items: t.Generator[USApplication, None, None]

    def project(
        self, attributes: t.List[str] = None, transaction_codes: t.List[UsptoPedsTransactionEventType] = None
    ) -> t.Generator[ResultDictType, None, None]:
        transaction_codes = transaction_codes or []
        for item in self.items:

            # Apply attribute filter, or use all attributes.
            output: ResultDictType = self.get_attributes(item, attributes=attributes)

            # Apply transaction events filter, or use all transaction events.
            output["transactions"] = self.get_transactions(item, codes=transaction_codes)

            yield output

    @staticmethod
    def get_attributes(item: USApplication, attributes: t.List[str] = None) -> ResultDictType:
        data = item.to_dict()
        output: ResultDictType = OrderedDict()
        if attributes:
            for attribute in attributes:
                output[attribute] = data.get(attribute)
        else:
            output = data
        return output

    @staticmethod
    def get_transactions(
        item: USApplication, codes: t.List[UsptoPedsTransactionEventType] = None
    ) -> t.List[TransactionDictType]:
        codes = codes or []
        codes_real: t.List[UsptoPedsTransactionEvent] = []
        for code in codes:
            if isinstance(code, str):
                try:
                    value = getattr(UsptoPedsTransactionEvent, code)
                    codes_real.append(value)
                except AttributeError:
                    raise AttributeError(
                        f"Unknown transaction event code '{code}'. "
                        f"Use one of {UsptoPedsTransactionEvent._member_names_}"
                    )
            else:
                codes_real.append(code)

        results: t.List[TransactionDictType] = []
        for transaction in item.transactions:
            if not codes or transaction.code in codes_real:
                results.append(transaction.to_dict())
        return results

    @staticmethod
    def to_json(data, limit: int = None) -> str:
        if limit is None:
            if isinstance(data, t.Generator):
                output = list(data)
            else:
                output = data
        else:
            output = []
            for _ in range(limit):
                try:
                    output.append(next(data))
                except StopIteration:
                    break

        return json.dumps(output, cls=JsonEncoder, indent=2)


class UsptoPedsClient:

    PAGESIZE = 50

    def query(
        self,
        app_status: t.Union[UsptoPedsAppStatus, str] = None,
        app_entity_status: str = None,
        patent_issue_date_begin: datetime.datetime = None,
        patent_issue_date_end: datetime.datetime = None,
        order_by: str = None,
    ) -> UsptoPedsResponse:

        filter_kwargs = OrderedDict()

        if app_status is not None:
            if isinstance(app_status, str):
                try:
                    app_status = UsptoPedsAppStatus[app_status]
                except KeyError:
                    raise KeyError(
                        f"Unknown status '{app_status}'. " f"Use one of {UsptoPedsAppStatus._member_names_}."
                    )
            filter_kwargs["app_status"] = app_status.value

        if app_entity_status is not None:
            filter_kwargs["app_entity_status"] = app_entity_status

        if patent_issue_date_begin is not None:
            if patent_issue_date_end is None:
                patent_issue_date_end = datetime.datetime.now()
            filter_kwargs["patent_issue_date"] = self.format_daterange(patent_issue_date_begin, patent_issue_date_end)

        logger.info(f"Setting page size: {self.PAGESIZE}")
        USApplicationManager.page_size = self.PAGESIZE

        logger.info(f"Applying filter:   {dict(filter_kwargs)}")
        logger.info(f"Applying order_by: {order_by}")
        applications = USApplication.objects.filter(**filter_kwargs)
        if order_by is not None:
            applications = applications.order_by(order_by)

        logger.info(f"Effective filter:  {applications.config.filter}")
        logger.info(f"Effective query:   {applications.query_params(page_no=0)}")

        return UsptoPedsResponse(count=applications.count(), items=applications)

    @staticmethod
    def format_daterange(date_begin: datetime.datetime, date_end: datetime.datetime):
        date_begin_str = rfc3339.format(date_begin, utc=True)
        date_end_str = rfc3339.format(date_end, utc=True)
        date_range = f"[{date_begin_str} TO {date_end_str}]"
        return date_range


def main():
    """
    Get issued patents with the following information:

    - Status
    - Patent title
    - Patent number
    - Patent issue date
    - Assignments
    - Applicants
    - Transaction events, filtered by event code relevant
      to allowance and issuance information.

    """

    setup_logging()

    peds = UsptoPedsClient()

    # Last 7 days, in reverse-chronological order.
    result = peds.query(
        app_status=UsptoPedsAppStatus.PATENTED,
        patent_issue_date_begin=datetime.datetime.now() - datetime.timedelta(days=7),
        order_by="-patent_issue_date",
    )

    # Since 2012, in chronological order.
    """
    import dateutil.parser
    result = peds.query(
        app_status=UsptoPedsAppStatus.PATENTED,
        patent_issue_date_begin=dateutil.parser.parse("2012-01-01T00:00:00Z"),
        order_by="patent_issue_date",
    )
    """

    logger.info(f"Hit count: {result.count}")
    results = result.project(
        attributes=["app_status", "patent_title", "patent_number", "patent_issue_date", "assignments", "applicants"],
        transaction_codes=[
            UsptoPedsTransactionEvent.ALLOWANCE_NOTICE_VERIFICATION_COMPLETED,
            UsptoPedsTransactionEvent.ALLOWANCE_NOTICE_MAILED,
            UsptoPedsTransactionEvent.ISSUANCE_CONSIDERED_READY,
            UsptoPedsTransactionEvent.ISSUANCE_NOTIFICATION_MAILED,
        ],
    )

    # print(result.to_json(results_final, limit=10))

    for result_final in results:
        print(result.to_json(result_final))


if __name__ == "__main__":
    """
    Synopsis::

        python -m patzilla.access.uspto.peds.api | jq
    """
    main()
