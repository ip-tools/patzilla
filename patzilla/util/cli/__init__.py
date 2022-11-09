import enum
import typing as t

import click


class EnumChoice(click.Choice):
    """
    Python Enum support for click.Choice

    https://github.com/pallets/click/issues/605
    https://github.com/pallets/click/pull/2210
    """
    def __init__(self, enum_type: t.Type[enum.Enum], case_sensitive: bool = True):
        super().__init__(
            choices=[element.name for element in enum_type],
            case_sensitive=case_sensitive,
        )
        self.enum_type = enum_type

    def convert(
        self, value: t.Any, param: t.Optional["click.Parameter"], ctx: t.Optional["click.Context"]
    ) -> t.Any:
        value = super().convert(value=value, param=param, ctx=ctx)
        if value is None:
            return None
        return self.enum_type[value]
