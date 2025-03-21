import typing as t

import alluka
import hikari

import arc
from arc.internal.types import ResponseBuilderT


class MockClient(arc.abc.Client[t.Any]):
    def __init__(
        self,
        app: t.Any,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflakeish | hikari.PartialGuild]
        | hikari.UndefinedType = hikari.UNDEFINED,
        autosync: bool = True,
        autodefer: bool | arc.AutodeferMode = True,
        default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
        is_nsfw: bool = False,
        integration_types: t.Sequence[hikari.ApplicationIntegrationType] = [
            hikari.ApplicationIntegrationType.GUILD_INSTALL
        ],
        invocation_contexts: t.Sequence[hikari.ApplicationContextType] = [
            hikari.ApplicationContextType.BOT_DM,
            hikari.ApplicationContextType.GUILD,
            hikari.ApplicationContextType.PRIVATE_CHANNEL,
        ],
        provided_locales: t.Sequence[hikari.Locale] | None = None,
        injector: alluka.abc.Client | None = None,
    ) -> None:
        super().__init__(
            app,
            default_enabled_guilds=default_enabled_guilds,
            autosync=autosync,
            autodefer=autodefer,
            default_permissions=default_permissions,
            is_nsfw=is_nsfw,
            integration_types=integration_types,
            invocation_contexts=invocation_contexts,
            provided_locales=provided_locales,
            injector=injector,
        )
        self._owner_ids: list[hikari.Snowflake] = [hikari.Snowflake(123456789)]

    @property
    def is_rest(self) -> bool:
        return True  # Setting it to True so we get back builders we can verify

    async def push_inter(self, interaction: hikari.CommandInteraction) -> ResponseBuilderT:
        builder = await self.on_command_interaction(interaction)
        if builder is None:
            raise arc.NoResponseIssuedError(
                f"No response was issued to interaction for command: {interaction.command_name} ({interaction.command_type})."
            )
        return builder

    async def push_autocomplete_inter(
        self, interaction: hikari.AutocompleteInteraction
    ) -> hikari.api.InteractionAutocompleteBuilder:
        builder = await self.on_autocomplete_interaction(interaction)
        if builder is None:
            raise arc.NoResponseIssuedError(
                f"No response was issued to autocomplete request for command: {interaction.command_name} ({interaction.command_type})."
            )
        return builder


class MockPlugin(arc.PluginBase[MockClient]):
    @property
    def is_rest(self) -> bool:
        return True


MockContext = arc.Context[MockClient]
