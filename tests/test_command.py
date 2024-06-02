import datetime

import hikari
import pytest
from hikari.users import UserImpl
from mock_client import MockClient, MockContext, MockPlugin

import arc

client = MockClient(hikari.GatewayBot(token="amongus"))


@pytest.fixture
def app() -> hikari.GatewayBot:
    return build_app()


def build_app() -> hikari.GatewayBot:
    return hikari.GatewayBot(token="amongus")


def build_user(app: hikari.GatewayBot, id: hikari.Snowflakeish = 123456789) -> hikari.User:
    return UserImpl(
        app=app,
        id=hikari.Snowflake(id),
        avatar_hash=None,
        banner_hash=None,
        global_name="Padoru",
        accent_color=None,
        flags=hikari.UserFlag.NONE,
        discriminator="1234",
        is_bot=False,
        is_system=False,
        username="Padoru",
    )


def build_member(
    app: hikari.GatewayBot,
    id: hikari.Snowflakeish = 123456789,
    *,
    role_ids: list[hikari.Snowflake] | None = None,
    permissions: hikari.Permissions | None = None,
) -> hikari.InteractionMember:
    return hikari.InteractionMember(
        guild_id=hikari.Snowflake(123456789),
        is_deaf=hikari.UNDEFINED,
        is_mute=hikari.UNDEFINED,
        is_pending=False,
        nickname=None,
        raw_communication_disabled_until=None,
        role_ids=role_ids or [],
        guild_avatar_hash=None,
        joined_at=datetime.datetime(2021, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
        permissions=permissions or hikari.Permissions.NONE,
        premium_since=None,
        user=build_user(app, id),
    )


def build_inter(
    app: hikari.GatewayBot,
    *,
    cmd_name: str,
    options: list[hikari.CommandInteractionOption] | None = None,
    resolved: hikari.ResolvedOptionData | None = None,
    author_id: hikari.Snowflakeish = 123456789,
    author_role_ids: list[hikari.Snowflake] | None = None,
    author_perms: hikari.Permissions | None = None,
) -> hikari.CommandInteraction:
    parts = cmd_name.split(" ")

    match len(parts):
        case 1:
            pass
        case 2:
            options = [
                hikari.CommandInteractionOption(
                    name=parts[1], type=hikari.OptionType.SUB_COMMAND, value=None, options=options
                )
            ]
        case 3:
            options = [
                hikari.CommandInteractionOption(
                    name=parts[1],
                    type=hikari.OptionType.SUB_COMMAND_GROUP,
                    value=None,
                    options=[
                        hikari.CommandInteractionOption(
                            name=parts[2], type=hikari.OptionType.SUB_COMMAND, value=None, options=options
                        )
                    ],
                )
            ]
        case _:
            raise ValueError("Invalid command name")

    return hikari.CommandInteraction(
        app=app,
        id=hikari.Snowflake(123456789),
        application_id=hikari.Snowflake(123456789),
        command_id=hikari.Snowflake(123456789),
        command_name=parts[0],
        command_type=hikari.CommandType.SLASH,
        entitlements=[],
        app_permissions=hikari.Permissions.all_permissions(),
        options=options,
        resolved=resolved,
        type=hikari.InteractionType.APPLICATION_COMMAND,
        token="padoru padoru",
        version=1,
        channel_id=hikari.Snowflake(123456789),
        guild_id=hikari.Snowflake(123456789),
        guild_locale="en-US",
        user=build_user(app, author_id),
        member=build_member(app, author_id, role_ids=author_role_ids, permissions=author_perms),
        locale="en-US",
    )


class PluginCanHandleError(Exception):
    pass


class GroupCanHandleError(Exception):
    pass


class SubgroupCanHandleError(Exception):
    pass


class CommandCanHandleError(Exception):
    pass


@client.include
@arc.slash_command("ping")
async def ping(ctx: MockContext) -> None:
    await ctx.respond("Pong!")


@client.include
@arc.with_hook(arc.owner_only)
@arc.slash_command("admin_ping")
async def ping_with_hook(ctx: MockContext) -> None:
    await ctx.respond("Pong!")


@client.include
@arc.with_hook(arc.owner_only)
@arc.slash_command("admin_ping_err")
async def ping_with_hook_err(ctx: MockContext) -> None:
    await ctx.respond("Pong!")


@ping_with_hook_err.set_error_handler
async def ping_with_hook_err_handler(ctx: MockContext, error: Exception) -> None:
    if isinstance(error, arc.NotOwnerError):
        await ctx.respond("❌ You are not the owner of the bot.")


@client.include
@arc.slash_command("sum")
async def sum(ctx: MockContext, a: arc.Option[int, arc.IntParams()], b: arc.Option[int, arc.IntParams()]) -> None:
    await ctx.respond(f"Sum: {a + b}")


plugin = MockPlugin("test")
group = plugin.include_slash_group("group")
subgroup = group.include_subgroup("subgroup")

client.add_plugin(plugin)


@subgroup.include
@arc.slash_subcommand("nested")
async def nested(ctx: MockContext) -> None:
    match ctx.author.id:
        case 1:
            raise CommandCanHandleError
        case 2:
            raise SubgroupCanHandleError
        case 3:
            raise GroupCanHandleError
        case 4:
            raise PluginCanHandleError
        case 5:
            raise Exception
        case _:
            await ctx.respond("Nested command!")


@nested.set_error_handler
async def nested_error_handler(ctx: MockContext, error: Exception) -> None:
    if isinstance(error, CommandCanHandleError):
        await ctx.respond("Command handled error")
        return
    raise error


@subgroup.set_error_handler
async def subgroup_error_handler(ctx: MockContext, error: Exception) -> None:
    if isinstance(error, SubgroupCanHandleError):
        await ctx.respond("Subgroup handled error")
        return
    raise error


@group.set_error_handler
async def group_error_handler(ctx: MockContext, error: Exception) -> None:
    if isinstance(error, GroupCanHandleError):
        await ctx.respond("Group handled error")
        return
    raise error


@plugin.set_error_handler
async def plugin_error_handler(ctx: MockContext, error: Exception) -> None:
    if isinstance(error, PluginCanHandleError):
        await ctx.respond("Plugin handled error")
        return
    raise error


@pytest.mark.asyncio
async def test_ping(app: hikari.GatewayBot) -> None:
    response = await client.push_inter(build_inter(app, cmd_name="ping"))
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Pong!"


@pytest.mark.asyncio
async def test_sum(app: hikari.GatewayBot) -> None:
    inter = build_inter(
        app,
        cmd_name="sum",
        options=[
            hikari.CommandInteractionOption(name="a", type=hikari.OptionType.INTEGER, value=3, options=None),
            hikari.CommandInteractionOption(name="b", type=hikari.OptionType.INTEGER, value=2, options=None),
        ],
    )
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Sum: 5"


@pytest.mark.asyncio
async def test_admin_ping(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, cmd_name="admin_ping")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Pong!"


@pytest.mark.asyncio
async def test_admin_ping_unprivileged(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=987654321, cmd_name="admin_ping")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    # Unhandled error
    assert response.content == "❌ Something went wrong. Please contact the bot developer."


@pytest.mark.asyncio
async def test_admin_ping_errhandler(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=987654321, cmd_name="admin_ping_err")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    # Handled error
    assert response.content == "❌ You are not the owner of the bot."


@pytest.mark.asyncio
async def test_nested_errhandler_ok(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=0, cmd_name="group subgroup nested")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Nested command!"


@pytest.mark.asyncio
async def test_nested_errhandler_cmdhandler(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=1, cmd_name="group subgroup nested")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Command handled error"


@pytest.mark.asyncio
async def test_nested_errhandler_subghandler(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=2, cmd_name="group subgroup nested")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Subgroup handled error"


@pytest.mark.asyncio
async def test_nested_errhandler_grphandler(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=3, cmd_name="group subgroup nested")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Group handled error"


@pytest.mark.asyncio
async def test_nested_errhandler_plghandler(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=4, cmd_name="group subgroup nested")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "Plugin handled error"


@pytest.mark.asyncio
async def test_nested_errhandler_unhandled(app: hikari.GatewayBot) -> None:
    inter = build_inter(app, author_id=5, cmd_name="group subgroup nested")
    response = await client.push_inter(inter)
    assert isinstance(response, hikari.impl.InteractionMessageBuilder)
    assert response.content == "❌ Something went wrong. Please contact the bot developer."
