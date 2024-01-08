import hikari

import arc

bot = hikari.GatewayBot("...", banner=None)
client = arc.GatewayClient(bot)


@client.include()
@arc.slash_command("test", default_permissions=hikari.Permissions.ADMINISTRATOR)
async def my_command(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    b: arc.Option[str, arc.StrParams(description="bar", min_length=100)],
    c: arc.Option[float | None, arc.FloatParams(description="baz", max=50.0)],
    d: arc.Option[hikari.GuildTextChannel | hikari.GuildNewsChannel | None, arc.ChannelParams(description="qux")],
    e: arc.Option[hikari.GuildChannel | None, arc.ChannelParams(description="quux")],
    f: arc.Option[hikari.Role | hikari.User, arc.MentionableParams(description="quuz")],
    g: arc.Option[hikari.Attachment | None, arc.AttachmentParams(description="among us")],
) -> None:
    pass


group = client.include_slash_group(
    "my_group", "My group description", default_permissions=hikari.Permissions.ADMINISTRATOR
)

subgroup = group.include_subgroup("my_subgroup", "My subgroup description")


@group.include
@arc.slash_subcommand("test_subcommand", "My subcommand description")
async def my_subcommand(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    b: arc.Option[str, arc.StrParams(description="bar", min_length=100)],
) -> None:
    pass


@subgroup.include()
@arc.slash_subcommand("test_subsubcommand", "My subsubcommand description")
async def my_subsubcommand(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    b: arc.Option[str, arc.StrParams(description="bar", min_length=100)],
) -> None:
    pass


def test_my_command() -> None:
    assert len(client._slash_commands) == 2

    command = client._slash_commands["test"]

    assert command.client is client

    assert command.name == "test"
    assert command.description == "No description provided."
    assert command.default_permissions == hikari.Permissions.ADMINISTRATOR
    assert command.is_dm_enabled is True
    assert command.is_nsfw is False
    assert command.name_localizations == {}
    assert command.description_localizations == {}

    assert isinstance(command, arc.SlashCommand)
    options = command.options

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
    assert options["f"].is_required

    assert isinstance(options["g"], arc.command.AttachmentOption)
    assert options["g"].name == "g"
    assert options["g"].description == "among us"
    assert not options["g"].is_required


def test_my_group() -> None:
    group = client._slash_commands["my_group"]
    assert isinstance(group, arc.SlashGroup)

    assert len(group.children) == 2
    assert group.client is client
    assert group.name == "my_group"
    assert group.description == "My group description"
    assert group.default_permissions == hikari.Permissions.ADMINISTRATOR
    assert group.is_dm_enabled is True
    assert group.is_nsfw is False
    assert group.name_localizations == {}
    assert group.description_localizations == {}

    subcmd = group.children["test_subcommand"]

    assert subcmd.client is client
    assert subcmd._parent is group
    assert subcmd.name == "test_subcommand"
    assert subcmd.description == "My subcommand description"
    assert isinstance(subcmd, arc.SlashSubCommand)
    assert isinstance(subcmd.options["a"], arc.command.IntOption)
    assert isinstance(subcmd.options["b"], arc.command.StrOption)

    subgroup = group.children["my_subgroup"]

    assert subgroup.client is client
    assert subgroup._parent is group
    assert subgroup.name == "my_subgroup"
    assert subgroup.description == "My subgroup description"
    assert isinstance(subgroup, arc.SlashSubGroup)
    assert len(subgroup.children) == 1

    subsubcmd = subgroup.children["test_subsubcommand"]
    assert subsubcmd.qualified_name == ("my_group", "my_subgroup", "test_subsubcommand")
