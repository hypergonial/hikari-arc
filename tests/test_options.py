import sys
import typing as t

import hikari
import pytest
import typing_extensions as te

from arc.abc.option import OptionType
from arc.context import Context
from arc.internal.options import OPTIONTYPE_TO_TYPE


def _get_literals(func: t.Callable[..., t.Any]) -> list[t.Any]:
    """Get all literals found in a function's overload's signatures."""
    literals: list[t.Any] = []
    for overload in te.get_overloads(func):
        hints = t.get_type_hints(overload)
        for hint in hints.values():
            if t.get_origin(hint) is t.Literal:
                # This is a Literal
                args = t.get_args(hint)
                literals.extend(args)
    return literals


def test_optiontype_has_all_hikari_option_types() -> None:
    for option_type in hikari.OptionType:
        try:
            OptionType(int(option_type))
        except Exception as e:
            raise AssertionError(f"Missing {option_type!r} in arc.OptionType enum.") from e


def test_context_get_option_has_all_option_overloads() -> None:
    # Do not test on 3.10-, as it does not support Literal
    if sys.version_info.minor <= 10:
        pytest.skip("Literal is not supported in Python 3.10 or lower")

    literals = _get_literals(Context.get_option)  # type: ignore

    for option_type in OptionType:
        if option_type is OptionType.SUB_COMMAND or option_type is OptionType.SUB_COMMAND_GROUP:
            continue

        assert option_type in literals, f"Missing {option_type!r} in Context.get_option overloads."


def test_options_mapping_contains_all_options() -> None:
    for option_type in OptionType:
        if option_type is OptionType.SUB_COMMAND or option_type is OptionType.SUB_COMMAND_GROUP:
            continue

        assert option_type in OPTIONTYPE_TO_TYPE, f"Missing {option_type!r} in OPTIONTYPE_TO_TYPE mapping."
