import hikari

import arc

bot = hikari.GatewayBot("...", banner=None)
client = arc.GatewayClient(bot)

group = client.include_slash_group(
    "my_group", "My group description", default_permissions=hikari.Permissions.ADMINISTRATOR
)

subgroup = group.include_subgroup("my_subgroup", "My subgroup description")


@client.include
@arc.message_command("Message Command")
async def message_cmd(ctx: arc.GatewayContext, message: hikari.Message) -> None:
    pass


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


def test_walk_commands() -> None:
    cmds = list(client.walk_commands(hikari.CommandType.SLASH, callable_only=False))

    assert len(cmds) == 4

    assert my_subcommand in cmds
    assert my_subsubcommand in cmds
    assert group in cmds
    assert subgroup in cmds

    cmds = list(client.walk_commands(hikari.CommandType.SLASH, callable_only=True))

    assert len(cmds) == 2

    assert my_subcommand in cmds
    assert my_subsubcommand in cmds

    cmds = list(client.walk_commands(hikari.CommandType.MESSAGE))

    assert len(cmds) == 1

    assert message_cmd in cmds
