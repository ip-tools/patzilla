import dataclasses
import datetime
import typing as t
from enum import Enum


def resolve_transaction_codes(codes):
    # Prepare list of events codes.
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
    return codes_real


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
class TransactionItem:
    date: datetime.date
    code: str
    description: str
