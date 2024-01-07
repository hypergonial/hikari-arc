import hikari

import arc

bot = hikari.GatewayBot("...", banner=None)
client = arc.GatewayClient(
    bot, autodefer=arc.AutodeferMode.EPHEMERAL, default_permissions=hikari.Permissions.MANAGE_GUILD, is_dm_enabled=False
)

plugin = arc.GatewayPlugin("foo", default_permissions=hikari.Permissions.NONE, is_dm_enabled=True)


@plugin.include
@arc.slash_command("foo", is_dm_enabled=False)
async def foo(ctx: arc.GatewayContext) -> None:
    await ctx.respond("foo")


@plugin.include
@arc.user_command("bar")
async def bar(ctx: arc.GatewayContext, user: hikari.User) -> None:
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
    assert foo.is_dm_enabled is False
    assert foo.default_permissions == hikari.Permissions.NONE
    assert foo.autodefer is arc.AutodeferMode.EPHEMERAL

    assert bar.is_dm_enabled is True
    assert bar.default_permissions == hikari.Permissions.NONE
    assert bar.autodefer is arc.AutodeferMode.EPHEMERAL

    assert baz.is_dm_enabled is False
    assert baz.default_permissions == hikari.Permissions.MANAGE_GUILD
    assert baz.autodefer is arc.AutodeferMode.ON

    assert qux.autodefer is arc.AutodeferMode.OFF
