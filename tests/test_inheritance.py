import hikari

import arc

bot = hikari.GatewayBot("...", banner=None)
client = arc.GatewayClient(
    bot,
    autodefer=arc.AutodeferMode.EPHEMERAL,
    default_permissions=hikari.Permissions.MANAGE_GUILD,
    invocation_contexts=[hikari.ApplicationContextType.GUILD],
    integration_types=[hikari.ApplicationIntegrationType.GUILD_INSTALL],
)

plugin = arc.GatewayPlugin(
    "foo",
    default_permissions=hikari.Permissions.NONE,
    integration_types=[hikari.ApplicationIntegrationType.GUILD_INSTALL, hikari.ApplicationIntegrationType.USER_INSTALL],
    invocation_contexts=[
        hikari.ApplicationContextType.BOT_DM,
        hikari.ApplicationContextType.GUILD,
        hikari.ApplicationContextType.PRIVATE_CHANNEL,
    ],
)


@plugin.include
@arc.slash_command("foo", invocation_contexts=[hikari.ApplicationContextType.GUILD])
async def foo(ctx: arc.GatewayContext) -> None:
    await ctx.respond("foo")


@plugin.include
@arc.user_command("bar")
async def bar(ctx: arc.GatewayContext, user: arc.Option[hikari.User, arc.UserParams()]) -> None:
    await ctx.respond(f"bar {user.mention}")


group = plugin.include_slash_group("group", "group description", autodefer=False)


@group.include
@arc.slash_subcommand("qux")
async def qux(ctx: arc.GatewayContext) -> None:
    await ctx.respond("foo")


client.add_plugin(plugin)


@client.include
@arc.message_command("baz", autodefer=True)
async def baz(ctx: arc.GatewayContext, message: hikari.Message) -> None:
    await ctx.respond(f"baz {message.author.mention}")


def test_settings_inheritance() -> None:
    assert foo.default_permissions == hikari.Permissions.NONE
    assert list(foo.integration_types) == [
        hikari.ApplicationIntegrationType.GUILD_INSTALL,
        hikari.ApplicationIntegrationType.USER_INSTALL,
    ]
    assert list(foo.invocation_contexts) == [hikari.ApplicationContextType.GUILD]
    assert foo.autodefer is arc.AutodeferMode.EPHEMERAL

    assert list(bar.integration_types) == [
        hikari.ApplicationIntegrationType.GUILD_INSTALL,
        hikari.ApplicationIntegrationType.USER_INSTALL,
    ]
    assert list(bar.invocation_contexts) == [
        hikari.ApplicationContextType.BOT_DM,
        hikari.ApplicationContextType.GUILD,
        hikari.ApplicationContextType.PRIVATE_CHANNEL,
    ]
    assert bar.default_permissions == hikari.Permissions.NONE
    assert bar.autodefer is arc.AutodeferMode.EPHEMERAL

    assert baz.default_permissions == hikari.Permissions.MANAGE_GUILD
    assert list(baz.integration_types) == [hikari.ApplicationIntegrationType.GUILD_INSTALL]
    assert list(baz.invocation_contexts) == [hikari.ApplicationContextType.GUILD]
    assert baz.autodefer is arc.AutodeferMode.ON

    assert qux.autodefer is arc.AutodeferMode.OFF
