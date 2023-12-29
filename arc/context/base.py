from __future__ import annotations

import asyncio
import datetime
import enum
import logging
import typing as t
from contextlib import suppress

import attr
import hikari

from ..internal.types import ClientT, ResponseBuilderT

if t.TYPE_CHECKING:
    from ..command import CallableCommandProto

__all__ = ("Context", "InteractionResponse", "AutodeferMode")

logger = logging.getLogger(__name__)


class AutodeferMode(enum.IntEnum):
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

    content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED
    flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED
    tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED
    component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED
    components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED
    attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED
    attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED
    embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED
    embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED
    mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED
    user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED
    role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED

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


class InteractionResponse:
    """Represents a response to an interaction, allows for standardized handling of responses.
    This class is not meant to be directly instantiated, and is instead returned by :obj:`arc.context.Context`.
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

        assert isinstance(self._context.interaction, (hikari.ComponentInteraction, hikari.ModalInteraction))
        return await self._context.interaction.fetch_initial_response()

    async def delete(self) -> None:
        """Delete the response issued to the interaction this object represents."""
        if self._message:
            await self._context.interaction.delete_message(self._message)
        else:
            await self._context.interaction.delete_initial_response()

    async def edit(
        self,
        content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
        *,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the message belonging to this response.

        Parameters
        ----------
        content : hikari.UndefinedOr[t.Any], optional
            The content of the message. Anything passed here will be cast to str.
        attachment : hikari.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : hikari.UndefinedOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : hikari.UndefinedOr[hikari.api.ComponentBuilder], optional
            A component to add to this message.
        components : hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : hikari.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : hikari.UndefinedOr[t.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : hikari.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool], optional
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


# TODO Add autodefer support from miru to this
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
        "_autodefer_task",
    )

    def __init__(
        self, client: ClientT, command: CallableCommandProto[ClientT], interaction: hikari.CommandInteraction
    ) -> None:
        self._client = client
        self._command = command
        self._interaction: hikari.CommandInteraction = interaction
        self._responses: t.MutableSequence[InteractionResponse] = []
        self._resp_builder: asyncio.Future[ResponseBuilderT] = asyncio.Future()
        self._issued_response: bool = False
        self._response_lock: asyncio.Lock = asyncio.Lock()
        self._created_at = datetime.datetime.now()
        self._autodefer_task: asyncio.Task[None] | None = None

    @property
    def interaction(self) -> hikari.CommandInteraction:
        """The underlying interaction object.

        .. warning::
            This should not be used directly in most cases, and is only exposed for advanced use cases.

            If you use the interaction to create a response in a view,
            you should disable the autodefer feature in your View.
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
        content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
        *,
        flags: int | hikari.MessageFlag | hikari.UndefinedType = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED,
        delete_after: hikari.UndefinedOr[float | int | datetime.timedelta] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """Short-hand method to create a new message response via the interaction this context represents.

        Parameters
        ----------
        content : hikari.UndefinedOr[Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : hikari.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : hikari.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : hikari.UndefinedOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : hikari.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : hikari.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : hikari.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : hikari.UndefinedOr[Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : hikari.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : int | hikari.MessageFlag | hikari.UndefinedType, optional
            Message flags that should be included with this message.
        delete_after: hikari.UndefinedOr[float | int | datetime.timedelta], optional
            Delete the response after the specified delay.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
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
        """Respond to the interaction with a builder.

        Parameters
        ----------
        builder : ResponseBuilderT
            The builder to respond with.

        Returns
        -------
        InteractionResponse | None
            A proxy object representing the response to the interaction. Will be None if the builder is a modal builder.
        """
        async with self._response_lock:
            if self._issued_response:
                raise RuntimeError("This interaction was already responded to.")

            if self.client.is_rest:
                self._resp_builder.set_result(builder)
                self._issued_response = True
                if not isinstance(builder, hikari.api.InteractionModalBuilder):
                    return await self._create_response()
                logger.debug(f"Created a new response for command '{self.command.name}'. Initial: True")
                return

            if isinstance(builder, hikari.api.InteractionMessageBuilder):
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
            elif isinstance(builder, hikari.api.InteractionDeferredBuilder):
                await self.interaction.create_initial_response(
                    response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=builder.flags
                )
            else:
                await self.interaction.create_modal_response(
                    title=builder.title, custom_id=builder.custom_id, components=builder.components
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
        """
        async with self._response_lock:
            if self._issued_response:
                raise RuntimeError("This interaction was already responded to.")

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

    async def edit_response(
        self,
        content: hikari.UndefinedNoneOr[t.Any] = hikari.UNDEFINED,
        *,
        component: hikari.UndefinedNoneOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedNoneOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedNoneOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedNoneOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedNoneOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedNoneOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the initial response belonging to this interaction.

        Parameters
        ----------
        content : hikari.UndefinedOr[Any], optional
            The content of the message. Anything passed here will be cast to str.
        attachment : hikari.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : hikari.UndefinedOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : hikari.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : hikari.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : hikari.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : hikari.UndefinedOr[Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : hikari.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialUser] | bool], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.PartialRole] | bool], optional
            The set of allowed role mentions in this message. Set to True to allow all.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.

        Raises
        ------
        RuntimeError
            The interaction was not yet responded to.
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
                raise RuntimeError("This interaction was not yet issued a response.")

    async def defer(self, flags: hikari.UndefinedOr[int | hikari.MessageFlag] = hikari.UNDEFINED) -> None:
        """Short-hand method to defer an interaction response. Raises RuntimeError if the interaction was already responded to.

        Parameters
        ----------
        flags : hikari.UndefinedOr[int | hikari.MessageFlag], optional
            Message flags that should be included with this defer request, by default None

        Raises
        ------
        RuntimeError
            REST clients cannot defer responses.
        ValueError
            response_type was not a deferred response type.
        """
        if self._issued_response:
            raise RuntimeError("Interaction was already responded to.")

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
