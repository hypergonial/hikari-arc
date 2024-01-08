import hikari

import arc

bot = hikari.GatewayBot("...", banner=None)
client = arc.GatewayClient(bot)


@client.include
@arc.user_command(name="Say Hi")
async def ping_user(ctx: arc.GatewayContext, user: hikari.User) -> None:
    await ctx.respond(f"Hi {user}!")


@client.include()
@arc.message_command(name="Say Hi")
async def ping_message(ctx: arc.GatewayContext, message: hikari.Message) -> None:
    await ctx.respond(f"Hi {message.author}!")


def test_user_command():
    assert len(client._user_commands) == 1
    command = client._user_commands["Say Hi"]

    assert command.name == "Say Hi"
    assert command.command_type is hikari.CommandType.USER
    assert command.qualified_name == ("Say Hi",)
    assert command.default_permissions is hikari.UNDEFINED
    assert command.is_dm_enabled is True
    assert command.is_nsfw is False
    assert command.name_localizations == {}


def test_message_command():
    assert len(client._message_commands) == 1
    command = client._message_commands["Say Hi"]

    assert command.name == "Say Hi"
    assert command.command_type is hikari.CommandType.MESSAGE
    assert command.qualified_name == ("Say Hi",)
    assert command.default_permissions is hikari.UNDEFINED
    assert command.is_dm_enabled is True
    assert command.is_nsfw is False
    assert command.name_localizations == {}
