import inspect

import hikari
import pytest

import arc
from arc.internal.sigparse import BASE_CHANNEL_TYPE_MAP, CHANNEL_TYPES_MAPPING, parse_command_signature


async def correct_command(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    b: arc.Option[str, arc.StrParams(description="bar", min_length=100)],
    c: arc.Option[float | None, arc.FloatParams(description="baz", max=50.0)],
    d: arc.Option[hikari.GuildTextChannel | hikari.GuildNewsChannel | None, arc.ChannelParams(description="qux")],
    e: arc.Option[hikari.GuildChannel | None, arc.ChannelParams(description="quux")],
    f: arc.Option[hikari.Role | hikari.User | None, arc.MentionableParams(description="quuz")] = None,
    g: arc.Option[hikari.Attachment | None, arc.AttachmentParams(description="among us")] = None,
    h: arc.Option[bool, arc.BoolParams(description="among us")] = False,
    i: arc.Option[str, arc.StrParams(description="foo")] = "among us",
) -> None:
    pass


def test_correct_command() -> None:
    options = parse_command_signature(correct_command)
    assert len(options) == 9

    assert isinstance(options["a"], arc.command.IntOption)
    assert options["a"].name == "a"
    assert options["a"].description == "foo"
    assert options["a"].is_required
    assert options["a"].min == 10
    assert options["a"].max is None

    assert isinstance(options["b"], arc.command.StrOption)
    assert options["b"].name == "b"
    assert options["b"].description == "bar"
    assert options["b"].is_required
    assert options["b"].min_length == 100
    assert options["b"].max_length is None

    assert isinstance(options["c"], arc.command.FloatOption)
    assert options["c"].name == "c"
    assert options["c"].description == "baz"
    assert not options["c"].is_required
    assert options["c"].min is None
    assert options["c"].max == 50.0

    assert isinstance(options["d"], arc.command.ChannelOption)
    assert options["d"].name == "d"
    assert options["d"].description == "qux"
    assert not options["d"].is_required
    assert options["d"].channel_types is not None
    assert set(options["d"].channel_types) == {hikari.ChannelType.GUILD_TEXT, hikari.ChannelType.GUILD_NEWS}

    assert isinstance(options["e"], arc.command.ChannelOption)
    assert options["e"].name == "e"
    assert options["e"].description == "quux"
    assert not options["e"].is_required
    assert options["e"].channel_types is not None
    assert set(options["e"].channel_types) == {
        hikari.ChannelType.GUILD_TEXT,
        hikari.ChannelType.GUILD_VOICE,
        hikari.ChannelType.GUILD_CATEGORY,
        hikari.ChannelType.GUILD_NEWS,
        hikari.ChannelType.GUILD_FORUM,
        hikari.ChannelType.GUILD_NEWS_THREAD,
        hikari.ChannelType.GUILD_PUBLIC_THREAD,
        hikari.ChannelType.GUILD_PRIVATE_THREAD,
        hikari.ChannelType.GUILD_STAGE,
    }

    assert isinstance(options["f"], arc.command.MentionableOption)
    assert options["f"].name == "f"
    assert options["f"].description == "quuz"
    assert not options["f"].is_required

    assert isinstance(options["g"], arc.command.AttachmentOption)
    assert options["g"].name == "g"
    assert options["g"].description == "among us"
    assert not options["g"].is_required

    assert isinstance(options["h"], arc.command.BoolOption)
    assert options["h"].name == "h"
    assert options["h"].description == "among us"
    assert not options["h"].is_required

    assert isinstance(options["i"], arc.command.StrOption)
    assert options["i"].name == "i"
    assert options["i"].description == "foo"
    assert not options["i"].is_required


async def wrong_params_type(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    b: arc.Option[str, arc.IntParams(description="bar", max=50)],
) -> None:
    pass


def test_wrong_params_type() -> None:
    with pytest.raises(TypeError):
        parse_command_signature(wrong_params_type)


class WrongType:
    pass


async def wrong_opt_type(ctx: arc.GatewayContext, a: arc.Option[WrongType, arc.IntParams(description="foo")]) -> None:
    pass


def test_wrong_opt_type() -> None:
    with pytest.raises(TypeError):
        parse_command_signature(wrong_opt_type)


class MyType:
    def __init__(self, val: int) -> None:
        self.val = val


async def di_annotation(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    c: arc.Option[str, arc.StrParams(name="b", description="bar", min_length=100)],
    b: MyType = arc.inject(),
) -> None:
    pass


def test_di_annotation() -> None:
    options = parse_command_signature(di_annotation)
    assert len(options) == 2

    assert isinstance(options["a"], arc.command.IntOption)
    assert options["a"].name == "a"
    assert options["a"].description == "foo"
    assert options["a"].is_required
    assert options["a"].min == 10
    assert options["a"].max is None

    assert isinstance(options["c"], arc.command.StrOption)
    assert options["c"].name == "b"
    assert options["c"].description == "bar"
    assert options["c"].is_required
    assert options["c"].min_length == 100
    assert options["c"].max_length is None


def test_ensure_parse_channel_types_has_every_channel_class() -> None:
    for _, attribute in inspect.getmembers(
        hikari, lambda a: isinstance(a, type) and issubclass(a, hikari.PartialChannel)
    ):
        result = CHANNEL_TYPES_MAPPING.get(attribute)

        assert result is not None, f"Missing channel type for {attribute} in CHANNEL_TYPES_MAPPING"


def test_ensure_base_channels_has_every_channel_type() -> None:
    for channel_type in hikari.ChannelType:
        assert channel_type in BASE_CHANNEL_TYPE_MAP.values()


# MIT License
#
# Copyright (c) 2023-present hypergonial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
