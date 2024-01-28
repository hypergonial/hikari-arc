from __future__ import annotations

import asyncio
import datetime
import enum
import logging
import typing as t
from contextlib import suppress

import attr
import hikari

from arc.abc.option import OptionType  # noqa: TCH001 Needed for tests
from arc.errors import NoResponseIssuedError, ResponseAlreadyIssuedError
from arc.internal.options import OPTIONTYPE_TO_TYPE, resolve_snowflake_value
from arc.internal.types import ClientT, ResponseBuilderT
from arc.locale import CustomLocaleRequest

if t.TYPE_CHECKING:
    from arc.abc.command import CallableCommandProto

__all__ = ("Context", "InteractionResponse", "AutodeferMode")

logger = logging.getLogger(__name__)


@t.final
class AutodeferMode(enum.IntEnum):
    """An enum representing autodefer configuration."""

    OFF = 0
    """Do not autodefer."""

    ON = 1
    """Autodefer if the command takes longer than 2 seconds to respond."""

    EPHEMERAL = 2
    """Autodefer and make the response ephemeral if the command takes longer than 2 seconds to respond."""

    @property
    def should_autodefer(self) -> bool:
        """Whether this mode should autodefer."""
        return self is not self.OFF


@attr.define(slots=True)
class _ResponseGlue:
    """A glue object to allow for easy creation of responses in both REST and Gateway contexts."""

    content: t.Any | hikari.UndefinedType = hikari.UNDEFINED
    flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED
    tts: bool | hikari.UndefinedType = hikari.UNDEFINED
    component: hikari.api.ComponentBuilder | hikari.UndefinedType = hikari.UNDEFINED
    components: t.Sequence[hikari.api.ComponentBuilder] | hikari.UndefinedType = hikari.UNDEFINED
    attachment: hikari.Resourceish | hikari.UndefinedType = hikari.UNDEFINED
    attachments: t.Sequence[hikari.Resourceish] | hikari.UndefinedType = hikari.UNDEFINED
    embed: hikari.Embed | hikari.UndefinedType = hikari.UNDEFINED
    embeds: t.Sequence[hikari.Embed] | hikari.UndefinedType = hikari.UNDEFINED
    mentions_everyone: bool | hikari.UndefinedType = hikari.UNDEFINED
    user_mentions: t.Sequence[hikari.Snowflakeish | hikari.PartialUser] | bool | hikari.UndefinedType = hikari.UNDEFINED
    role_mentions: t.Sequence[hikari.Snowflakeish | hikari.PartialRole] | bool | hikari.UndefinedType = hikari.UNDEFINED

    def _to_dict(self) -> dict[str, t.Any]:
        return {
            "content": self.content,
            "flags": self.flags,
            "tts": self.tts,
            "component": self.component,
            "components": self.components,
            "attachment": self.attachment,
            "attachments": self.attachments,
            "embed": self.embed,
            "embeds": self.embeds,
            "mentions_everyone": self.mentions_everyone,
            "user_mentions": self.user_mentions,
            "role_mentions": self.role_mentions,
        }

    def _to_builder(self) -> hikari.api.InteractionMessageBuilder:
        components: list[hikari.api.ComponentBuilder] = list(self.components) if self.components else []
        attachments: list[hikari.Resourceish] = list(self.attachments) if self.attachments else []
        embeds: list[hikari.Embed] = list(self.embeds) if self.embeds else []

        return hikari.impl.InteractionMessageBuilder(
            type=hikari.ResponseType.MESSAGE_CREATE,
            content=self.content,
            flags=self.flags,
            components=components or ([self.component] if self.component else hikari.UNDEFINED),
            attachments=attachments or ([self.attachment] if self.attachment else hikari.UNDEFINED),
            embeds=embeds or ([self.embed] if self.embed else hikari.UNDEFINED),
            mentions_everyone=self.mentions_everyone,
            user_mentions=self.user_mentions,
            role_mentions=self.role_mentions,
        )


@t.final
class InteractionResponse:
    """Represents a message response to an interaction, allows for standardized handling of such responses.
    This class is not meant to be directly instantiated, and is instead returned by [Context][arc.context.base.Context]
    when a message response is issued.
    """

    __slots__ = ("_context", "_message", "_delete_after_task")

    def __init__(self, context: Context[ClientT], message: hikari.Message | None = None) -> None:
        self._context: Context[ClientT] = context
        self._message: hikari.Message | None = message
        self._delete_after_task: asyncio.Task[None] | None = None

    def __await__(self) -> t.Generator[t.Any, None, hikari.Message]:
        return self.retrieve_message().__await__()

    async def _do_delete_after(self, delay: float) -> None:
        """Delete the response after the specified delay.

        This should not be called manually,
        and instead should be triggered by the `delete_after` method of this class.
        """
        await asyncio.sleep(delay)
        await self.delete()

    def delete_after(self, delay: int | float | datetime.timedelta) -> None:
        """Delete the response after the specified delay.

        Parameters
        ----------
        delay : int | float | datetime.timedelta
            The delay after which the response should be deleted.
        """
        if self._delete_after_task is not None:
            raise RuntimeError("A delete_after task is already running.")

        if isinstance(delay, datetime.timedelta):
            delay = delay.total_seconds()
        self._delete_after_task = asyncio.create_task(self._do_delete_after(delay))

    async def retrieve_message(self) -> hikari.Message:
        """Get or fetch the message created by this response.
        Initial responses need to be fetched, while followups will be provided directly.

        !!! note
            The object itself can also be awaited directly, which in turn calls this method,
            producing the same results.

        Returns
        -------
        hikari.Message
            The message created by this response.
        """
        if self._message:
            return self._message

        return await self._context.interaction.fetch_initial_response()

    async def delete(self) -> None:
        """Delete the response issued to the interaction this object represents."""
        if self._message:
            await self._context.interaction.delete_message(self._message)
        else:
            await self._context.interaction.delete_initial_response()

    async def edit(
        self,
        content: t.Any | hikari.UndefinedType | None = hikari.UNDEFINED,
        *,
        component: hikari.api.ComponentBuilder | hikari.UndefinedType | None = hikari.UNDEFINED,
        components: t.Sequence[hikari.api.ComponentBuilder] | hikari.UndefinedType | None = hikari.UNDEFINED,
        attachment: hikari.Resourceish | hikari.UndefinedType | None = hikari.UNDEFINED,
        attachments: t.Sequence[hikari.Resourceish] | hikari.UndefinedType | None = hikari.UNDEFINED,
        embed: hikari.Embed | hikari.UndefinedType | None = hikari.UNDEFINED,
        embeds: t.Sequence[hikari.Embed] | hikari.UndefinedType | None = hikari.UNDEFINED,
        mentions_everyone: bool | hikari.UndefinedType = hikari.UNDEFINED,
        user_mentions: t.Sequence[hikari.Snowflakeish | hikari.PartialUser]
        | bool
        | hikari.UndefinedType = hikari.UNDEFINED,
        role_mentions: t.Sequence[hikari.Snowflakeish | hikari.PartialRole]
        | bool
        | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the message belonging to this response.

        Parameters
        ----------
        content : t.Any | hikari.UndefinedType
            The content of the message. Anything passed here will be cast to str.
        attachment : hikari.Resourceish | hikari.UndefinedType
            An attachment to add to this message.
        attachments : t.Sequence[hikari.Resourceish] | hikari.UndefinedType
            A sequence of attachments to add to this message.
        component : hikari.api.ComponentBuilder | hikari.UndefinedType
            A component to add to this message.
        components : t.Sequence[hikari.api.ComponentBuilder] | hikari.UndefinedType
            A sequence of components to add to this message.
        embed : hikari.Embed | hikari.UndefinedType
            An embed to add to this message.
        embeds : t.Sequence[hikari.Embed] | hikari.UndefinedType
            A sequence of embeds to add to this message.
        mentions_everyone : bool | hikari.UndefinedType
            If True, mentioning @everyone will be allowed.
        user_mentions : t.Sequence[hikari.Snowflakish | hikari.PartialUser] | bool | hikari.UndefinedType
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : t.Sequence[hikari.Snowflakish | hikari.PartialRole] | bool | hikari.UndefinedType
            The set of allowed role mentions in this message. Set to True to allow all.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        if self._message:
            message = await self._context.interaction.edit_message(
                self._message,
                content,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )
        else:
            message = await self._context.interaction.edit_initial_response(
                content,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )
        return await self._context._create_response(message)


@t.final
class Context(t.Generic[ClientT]):
    """A context object that is proxying a Discord command interaction."""

    __slots__ = (
        "_client",
        "_command",
        "_interaction",
        "_responses",
        "_resp_builder",
        "_issued_response",
        "_response_lock",
        "_autodefer_task",
        "_created_at",
        "_has_command_failed",
        "_options",
    )

    def __init__(
        self, client: ClientT, command: CallableCommandProto[ClientT], interaction: hikari.CommandInteraction
    ) -> None:
        self._client = client
        self._command = command
        self._interaction: hikari.CommandInteraction = interaction
        self._options: t.Sequence[hikari.CommandInteractionOption] | None = None
        self._responses: t.MutableSequence[InteractionResponse] = []
        self._resp_builder: asyncio.Future[ResponseBuilderT] = asyncio.Future()
        self._issued_response: bool = False
        self._response_lock: asyncio.Lock = asyncio.Lock()
        self._created_at = datetime.datetime.now()
        self._autodefer_task: asyncio.Task[None] | None = None
        self._has_command_failed: bool = False

    @property
    def interaction(self) -> hikari.CommandInteraction:
        """The underlying interaction object.

        !!! warning
            This should not be used directly in most cases, and is only exposed for advanced use cases.

            If you use the interaction to create a response,
            you should disable the autodefer feature in your command.
        """
        return self._interaction

    @property
    def responses(self) -> t.Sequence[InteractionResponse]:
        """A list of all responses issued to the interaction this context is proxying."""
        return self._responses

    @property
    def client(self) -> ClientT:
        """The client that included the command."""
        return self._client

    @property
    def command(self) -> CallableCommandProto[ClientT]:
        """The command that was invoked."""
        return self._command

    @property
    def user(self) -> hikari.User:
        """The user who triggered this interaction."""
        return self._interaction.user

    @property
    def author(self) -> hikari.User:
        """Alias for Context.user."""
        return self.user

    @property
    def member(self) -> hikari.InteractionMember | None:
        """The member who triggered this interaction. Will be None in DMs."""
        return self._interaction.member

    @property
    def locale(self) -> str | hikari.Locale:
        """The locale of this context."""
        return self._interaction.locale

    @property
    def guild_locale(self) -> str | hikari.Locale | None:
        """The guild locale of this context, if in a guild.
        This will default to `en-US` if not a community guild.
        """
        return self._interaction.guild_locale

    @property
    def app_permissions(self) -> hikari.Permissions | None:
        """The permissions of the bot. Will be None in DMs."""
        return self._interaction.app_permissions

    @property
    def channel_id(self) -> hikari.Snowflake:
        """The ID of the channel the context represents."""
        return self._interaction.channel_id

    @property
    def guild_id(self) -> hikari.Snowflake | None:
        """The ID of the guild the context represents. Will be None in DMs."""
        return self._interaction.guild_id

    @property
    def is_valid(self) -> bool:
        """Returns if the underlying interaction expired or not.
        This is not 100% accurate due to API latency, but should be good enough for most use cases.
        """
        if self._issued_response:
            return datetime.datetime.now() - self._created_at <= datetime.timedelta(minutes=15)
        else:
            return datetime.datetime.now() - self._created_at <= datetime.timedelta(seconds=3)

    @property
    def issued_response(self) -> bool:
        """Whether this interaction was already issued an initial response."""
        return self._issued_response

    @property
    def has_command_failed(self) -> bool:
        """Returns if the command callback failed to execute or not."""
        return self._has_command_failed

    def _start_autodefer(self, autodefer_mode: AutodeferMode) -> None:
        """Start the autodefer task."""
        if self._autodefer_task is not None:
            raise RuntimeError("Context autodefer task already started")

        self._autodefer_task = asyncio.create_task(self._autodefer(autodefer_mode))

    async def _autodefer(self, autodefer_mode: AutodeferMode) -> None:
        """Automatically defer the interaction after 2 seconds. This should be started as a task."""
        await asyncio.sleep(2)

        async with self._response_lock:
            if self._issued_response:
                return
            logger.debug(f"Autodeferring an interaction for command '{self.command.name}'.")
            flags = hikari.MessageFlag.EPHEMERAL if autodefer_mode is AutodeferMode.EPHEMERAL else hikari.UNDEFINED
            # ctx.defer() also acquires _response_lock so we need to use self._interaction directly
            if not self.client.is_rest:
                await self._interaction.create_initial_response(
                    hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=flags
                )
            else:
                self._resp_builder.set_result(
                    hikari.impl.InteractionDeferredBuilder(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=flags)
                )
            self._issued_response = True
            await self._create_response()

    async def _create_response(self, message: hikari.Message | None = None) -> InteractionResponse:
        """Create a new response and add it to the list of tracked responses.

        If an autodefer task is running, it will be cancelled, unless cancel_autodefer is False.
        """
        if self._autodefer_task is not None:
            self._autodefer_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._autodefer_task
            self._autodefer_task = None

        response = InteractionResponse(self, message)
        self._responses.append(response)
        logger.debug(f"Created a new response for command '{self.command.name}'. Initial: {not bool(message)}")
        return response

    def get_guild(self) -> hikari.GatewayGuild | None:
        """Gets the guild this context represents, if any. Requires application cache."""
        return self._interaction.get_guild()

    def get_channel(self) -> hikari.TextableGuildChannel | None:
        """Gets the channel this context represents, None if in a DM. Requires application cache."""
        return self._interaction.get_channel()

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.ATTACHMENT]) -> hikari.Attachment | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.MENTIONABLE]) -> hikari.User | hikari.Role | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.USER]) -> hikari.User | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.ROLE]) -> hikari.Role | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.CHANNEL]) -> hikari.PartialChannel | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.STRING]) -> str | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.BOOLEAN]) -> bool | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.FLOAT]) -> float | None:
        ...

    @t.overload
    def get_option(self, name: str, opt_type: t.Literal[OptionType.INTEGER]) -> int | None:
        ...

    def get_option(self, name: str, opt_type: OptionType) -> t.Any | None:
        """Get the value of an option by name.

        Parameters
        ----------
        name : str
            The name of the option.
        opt_type : hikari.OptionType
            The type of the option.

        Returns
        -------
        ValueT | None
            The value of the option, or None if it does not exist, or is not of the correct type.

        Examples
        --------
        ```py
        value = ctx.get_option("name", arc.OptionType.STRING)
        if value is None:
            # Option does not exist or is not a string

        # Do something with the value
        print(value)
        ```

        """
        if self._options is None:
            return None

        value = next((x.value for x in self._options if x.name == name), None)

        if value is hikari.Snowflake and self._interaction.resolved is not None:
            value = resolve_snowflake_value(value, opt_type, self._interaction.resolved)

        if not isinstance(value, OPTIONTYPE_TO_TYPE[opt_type]):
            return None

        return value

    def loc(self, key: str, use_guild: bool = True, force_locale: hikari.Locale | None = None, **kwargs: t.Any) -> str:
        """Get a localized string using the interaction's locale.

        Parameters
        ----------
        key : str
            The key of the string to localize.
        use_guild : bool
            Whether to use the guild or not, if in a guild.
        force_locale : hikari.Locale | None
            Force a locale to use, instead of the context's locale.
        kwargs : t.Any
            The keyword arguments to pass to the string formatter.

        Returns
        -------
        str
            The localized string.
        """
        if not self._client._provided_locales:
            raise RuntimeError("The client does not have any provided locales set.")

        if force_locale is None:
            if not isinstance(self.locale, hikari.Locale):
                raise RuntimeError("This context does not have a valid locale object.")

            if self.guild_locale and not isinstance(self.guild_locale, hikari.Locale):
                raise RuntimeError("This context does not have a valid guild locale object.")

            locale = (self.guild_locale or self.locale) if use_guild else self.locale
        else:
            locale = force_locale

        if not self._client._custom_locale_provider:
            raise RuntimeError("The client does not have a custom locale provider.")

        if locale not in self._client._provided_locales:
            locale = hikari.Locale.EN_US

        request = CustomLocaleRequest(self.command, locale, self, key)
        return self._client._custom_locale_provider(request).format(**kwargs)

    async def get_last_response(self) -> InteractionResponse:
        """Get the last response issued to the interaction this context is proxying.

        Returns
        -------
        InteractionResponse
            The response object.

        Raises
        ------
        RuntimeError
            The interaction was not yet responded to.
        """
        if self._responses:
            return self._responses[-1]
        raise RuntimeError("This interaction was not yet issued a response.")

    async def respond(
        self,
        content: t.Any | hikari.UndefinedType = hikari.UNDEFINED,
        *,
        flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED,
        tts: bool | hikari.UndefinedType = hikari.UNDEFINED,
        attachment: hikari.Resourceish | hikari.UndefinedType = hikari.UNDEFINED,
        attachments: t.Sequence[hikari.Resourceish] | hikari.UndefinedType = hikari.UNDEFINED,
        component: hikari.api.ComponentBuilder | hikari.UndefinedType = hikari.UNDEFINED,
        components: t.Sequence[hikari.api.ComponentBuilder] | hikari.UndefinedType = hikari.UNDEFINED,
        embed: hikari.Embed | hikari.UndefinedType = hikari.UNDEFINED,
        embeds: t.Sequence[hikari.Embed] | hikari.UndefinedType = hikari.UNDEFINED,
        mentions_everyone: bool | hikari.UndefinedType = hikari.UNDEFINED,
        user_mentions: t.Sequence[hikari.Snowflakeish | hikari.PartialUser]
        | bool
        | hikari.UndefinedType = hikari.UNDEFINED,
        role_mentions: t.Sequence[hikari.Snowflake | hikari.PartialRole]
        | bool
        | hikari.UndefinedType = hikari.UNDEFINED,
        delete_after: float | int | datetime.timedelta | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """Short-hand method to create a new message response via the interaction this context represents.
        This function automatically determines if the response should be an initial response or a followup.

        Parameters
        ----------
        content : Any | hikari.UndefinedType
            The content of the message. Anything passed here will be cast to str.
        tts : bool | hikari.UndefinedType
            If the message should be tts or not.
        attachment : hikari.Resourceish | hikari.UndefinedType
            An attachment to add to this message.
        attachments : t.Sequence[hikari.Resourceish] | hikari.UndefinedType
            A sequence of attachments to add to this message.
        component : hikari.api.special_endpoints.ComponentBuilder | hikari.UndefinedType
            A component to add to this message.
        components : t.Sequence[hikari.api.special_endpoints.ComponentBuilder] | hikari.UndefinedType
            A sequence of components to add to this message.
        embed : hikari.Embed | hikari.UndefinedType
            An embed to add to this message.
        embeds : Sequence[hikari.Embed] | hikari.UndefinedType
            A sequence of embeds to add to this message.
        mentions_everyone : bool | hikari.UndefinedType
            If True, mentioning @everyone will be allowed.
        user_mentions : hikari.SnowflakeishSequence[hikari.PartialUser] | bool | hikari.UndefinedType
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : hikari.SnowflakeishSequence[hikari.PartialRole] | bool | hikari.UndefinedType
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : int | hikari.MessageFlag | hikari.UndefinedType
            Message flags that should be included with this message.
        delete_after: float | int | datetime.timedelta | hikari.UndefinedType
            Delete the response after the specified delay.

        Returns
        -------
        InteractionResponse
            A proxy object representing the message response to the interaction.
        """
        async with self._response_lock:
            if self._issued_response:
                message = await self.interaction.execute(
                    content,
                    tts=tts,
                    component=component,
                    components=components,
                    attachment=attachment,
                    attachments=attachments,
                    embed=embed,
                    embeds=embeds,
                    mentions_everyone=mentions_everyone,
                    user_mentions=user_mentions,
                    role_mentions=role_mentions,
                    flags=flags,
                )
                response = await self._create_response(message)
            else:
                glue = _ResponseGlue(
                    content=content,
                    flags=flags,
                    tts=tts,
                    component=component,
                    components=components,
                    attachment=attachment,
                    attachments=attachments,
                    embed=embed,
                    embeds=embeds,
                    mentions_everyone=mentions_everyone,
                    user_mentions=user_mentions,
                    role_mentions=role_mentions,
                )

                if not self.client.is_rest:
                    await self.interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE, **glue._to_dict()
                    )
                else:
                    self._resp_builder.set_result(glue._to_builder())

                self._issued_response = True
                response = await self._create_response()
            if delete_after:
                response.delete_after(delete_after)
            return response

    @t.overload
    async def respond_with_builder(self, builder: hikari.api.InteractionModalBuilder) -> None:
        ...

    @t.overload
    async def respond_with_builder(
        self, builder: hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder
    ) -> InteractionResponse:
        ...

    async def respond_with_builder(self, builder: ResponseBuilderT) -> InteractionResponse | None:
        """Respond to the interaction with a builder. This method will try to turn the builder into a valid
        response or followup, depending on the builder type and interaction state.

        Parameters
        ----------
        builder : ResponseBuilderT
            The builder to respond with.

        Returns
        -------
        InteractionResponse | None
            A proxy object representing the response to the interaction. Will be None if the builder is a modal builder.

        Raises
        ------
        RuntimeError
            The interaction was already issued an initial response and the builder can only be used for initial responses.
        """
        async with self._response_lock:
            if self._issued_response and not isinstance(builder, hikari.api.InteractionMessageBuilder):
                raise RuntimeError("This interaction was already issued an initial response.")

            if self.client.is_rest and not self._issued_response:
                self._resp_builder.set_result(builder)
                self._issued_response = True
                if not isinstance(builder, hikari.api.InteractionModalBuilder):
                    return await self._create_response()
                logger.debug(f"Created a new response for command '{self.command.name}'. Initial: True")
                return

            if isinstance(builder, hikari.api.InteractionMessageBuilder):
                if not self._issued_response:
                    await self.interaction.create_initial_response(
                        response_type=hikari.ResponseType.MESSAGE_CREATE,
                        content=builder.content,
                        tts=builder.is_tts,
                        components=builder.components,
                        attachments=builder.attachments,
                        embeds=builder.embeds,
                        mentions_everyone=builder.mentions_everyone,
                        user_mentions=builder.user_mentions,
                        role_mentions=builder.role_mentions,
                        flags=builder.flags,
                    )
                else:
                    await self.interaction.execute(
                        content=builder.content,
                        tts=builder.is_tts,
                        components=builder.components or hikari.UNDEFINED,
                        attachments=builder.attachments or hikari.UNDEFINED,
                        embeds=builder.embeds or hikari.UNDEFINED,
                        mentions_everyone=builder.mentions_everyone,
                        user_mentions=builder.user_mentions,
                        role_mentions=builder.role_mentions,
                        flags=builder.flags,
                    )
            elif isinstance(builder, hikari.api.InteractionDeferredBuilder):
                await self.interaction.create_initial_response(
                    response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=builder.flags
                )
            else:
                await self.interaction.create_modal_response(
                    title=builder.title, custom_id=builder.custom_id, components=builder.components or hikari.UNDEFINED
                )

            self._issued_response = True
            if not isinstance(builder, hikari.api.InteractionModalBuilder):
                return await self._create_response()
            logger.debug(f"Created a new response for command '{self.command.name}'. Initial: True")

    async def respond_with_modal(
        self, title: str, custom_id: str, *, components: t.Sequence[hikari.api.ComponentBuilder]
    ) -> None:
        """Respond to the interaction with a modal. Note that this **must be** the first response issued to the interaction.
        If you're using `miru`, or already have an interaction builder, use [`respond_with_builder`][arc.context.base.Context.respond_with_builder] instead.

        Parameters
        ----------
        title : str
            The title of the modal.
        custom_id : str
            The custom ID of the modal.
        components : t.Sequence[hikari.api.ComponentBuilder]
            The list of hikari component builders to add to the modal.

        Raises
        ------
        ResponseAlreadyIssuedError
            The interaction was already issued an initial response.
        """
        async with self._response_lock:
            if self._issued_response:
                raise ResponseAlreadyIssuedError("This interaction was already issued an initial response.")

            if self.client.is_rest:
                builder = hikari.impl.InteractionModalBuilder(
                    title=title, custom_id=custom_id, components=list(components)
                )
                self._resp_builder.set_result(builder)
            else:
                await self.interaction.create_modal_response(
                    title=title, custom_id=custom_id, components=list(components)
                )
            self._issued_response = True
            logger.debug(f"Created a new response for command '{self.command.name}'. Initial: True")

    async def edit_initial_response(
        self,
        content: t.Any | None | hikari.UndefinedType = hikari.UNDEFINED,
        *,
        attachment: hikari.Resourceish | None | hikari.UndefinedType = hikari.UNDEFINED,
        attachments: t.Sequence[hikari.Resourceish] | None | hikari.UndefinedType = hikari.UNDEFINED,
        component: hikari.api.ComponentBuilder | None | hikari.UndefinedType = hikari.UNDEFINED,
        components: t.Sequence[hikari.api.ComponentBuilder] | None | hikari.UndefinedType = hikari.UNDEFINED,
        embed: hikari.Embed | None | hikari.UndefinedType = hikari.UNDEFINED,
        embeds: t.Sequence[hikari.Embed] | None | hikari.UndefinedType = hikari.UNDEFINED,
        mentions_everyone: bool | hikari.UndefinedType = hikari.UNDEFINED,
        user_mentions: t.Sequence[hikari.Snowflakeish | hikari.PartialUser]
        | bool
        | hikari.UndefinedType = hikari.UNDEFINED,
        role_mentions: t.Sequence[hikari.Snowflake | hikari.PartialRole]
        | bool
        | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the initial response belonging to this interaction.

        If you want to edit a followup, you should use the [`edit()`][arc.context.base.InteractionResponse.edit]
        method of the returned [`InteractionResponse`][arc.context.base.InteractionResponse] response object instead.

        Parameters
        ----------
        content : t.Any | None | hikari.UndefinedType
            The content of the message. Anything passed here will be cast to str.
        attachment : hikari.Resourceish | None | hikari.UndefinedType
            An attachment to add to this message.
        attachments : t.Sequence[hikari.Resourceish] | None | hikari.UndefinedType
            A sequence of attachments to add to this message.
        component : hikari.api.ComponentBuilder | None | hikari.UndefinedType
            A component to add to this message.
        components : t.Sequence[hikari.api.ComponentBuilder] | None | hikari.UndefinedType
            A sequence of components to add to this message.
        embed : hikari.Embed | None | hikari.UndefinedType
            An embed to add to this message.
        embeds : t.Sequence[hikari.Embed] | None | hikari.UndefinedType
            A sequence of embeds to add to this message.
        mentions_everyone : bool | hikari.UndefinedType
            If True, mentioning @everyone will be allowed.
        user_mentions : t.Sequence[hikari.Snowflakeish | hikari.PartialUser] | bool | hikari.UndefinedType
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : t.Sequence[hikari.Snowflakeish | hikari.PartialRole] | bool | hikari.UndefinedType
            The set of allowed role mentions in this message. Set to True to allow all.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.

        Raises
        ------
        NoResponseIssuedError
            The interaction was not yet issued an initial response.
        """
        async with self._response_lock:
            if self._issued_response:
                message = await self.interaction.edit_initial_response(
                    content,
                    component=component,
                    components=components,
                    attachment=attachment,
                    attachments=attachments,
                    embed=embed,
                    embeds=embeds,
                    mentions_everyone=mentions_everyone,
                    user_mentions=user_mentions,
                    role_mentions=role_mentions,
                )
                return await self._create_response(message)

            else:
                raise NoResponseIssuedError("This interaction was not yet issued an initial response.")

    async def defer(self, flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED) -> None:
        """Short-hand method to defer an interaction response. Raises ResponseAlreadyIssuedError
        if the interaction was already responded to.

        Parameters
        ----------
        flags : int | hikari.MessageFlag | hikari.UndefinedType
            Message flags that should be included with this defer request

        Raises
        ------
        ResponseAlreadyIssuedError
            The interaction was already issued an initial response.
        """
        if self._issued_response:
            raise ResponseAlreadyIssuedError("Interaction was already issued an initial response.")

        async with self._response_lock:
            if not self.client.is_rest:
                await self.interaction.create_initial_response(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=flags)
            else:
                self._resp_builder.set_result(self._interaction.build_deferred_response().set_flags(flags))

            self._issued_response = True
            await self._create_response()


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
