import hikari

import arc

plugin = arc.GatewayPlugin("test_plugin")


@plugin.include
@arc.slash_command("foo", "Test description")
async def foo_command(
    ctx: arc.GatewayContext,
    a: arc.Option[float | None, arc.FloatParams(description="foo", max=50.0)],
    b: arc.Option[hikari.GuildChannel | None, arc.ChannelParams(description="bar")],
) -> None:
    pass


@plugin.include
@arc.slash_command("bar", "Test description")
async def bar_command(
    ctx: arc.GatewayContext,
    a: arc.Option[hikari.Role | hikari.User, arc.MentionableParams(description="foo")],
    b: arc.Option[hikari.Attachment | None, arc.AttachmentParams(description="bar")],
) -> None:
    pass


@plugin.include
@arc.slash_command("baz", "Test description")
async def baz_command(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    b: arc.Option[str, arc.StrParams(description="bar", min_length=100)],
) -> None:
    pass


group = plugin.include_slash_group(
    "my_group", "My group description", default_permissions=hikari.Permissions.ADMINISTRATOR
)


@group.include
@arc.slash_subcommand("test_subcommand", "My subcommand description")
async def my_subcommand(
    ctx: arc.GatewayContext,
    a: arc.Option[int, arc.IntParams(description="foo", min=10)],
    b: arc.Option[str, arc.StrParams(description="bar", min_length=100)],
) -> None:
    pass


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
