---
title: Options
description: A guide on slash command options
hide:
  - toc
---

# Options

Options can be used to ask for user input in slash commands. They come in a variety of types and support various features, depending on the type.

## Declaring options

An **option** can be declared as parameters in the command callback using the following general syntax:

```py
var_name: arc.Option[type, arc.TypeParams(...)]
```

Where `type` is a substitute for the type of the option.

This is what that looks like in action:

=== "Gateway"

    ```py
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.GatewayContext,
        number: arc.Option[int, arc.IntParams(description="A number")]
    ) -> None:
        await ctx.respond(f"You provided {number}!")
    ```

=== "REST"

    ```py
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.RESTContext,
        number: arc.Option[int, arc.IntParams(description="A number")]
    ) -> None:
        await ctx.respond(f"You provided {number}!")
    ```

To make an option **not required**, you should set a default value:

=== "Gateway"

    ```py
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.GatewayContext,
        number: arc.Option[int, arc.IntParams(description="A number")] = 10,
        user: arc.Option[hikari.User | None, arc.UserParams(description="A user.")] = None,
    ) -> None:
        await ctx.respond(f"You provided {number} and {user.mention if user else None}!")
    ```

=== "REST"

    ```py
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.RESTContext,
        number: arc.Option[int, arc.IntParams(description="A number")] = 10,
        user: arc.Option[hikari.User | None, arc.UserParams(description="A user.")] = None,
    ) -> None:
        await ctx.respond(f"You provided {number} and {user.mention if user else None}!")
    ```

### Supported option types

The following option types are supported:

- `bool` & [`arc.BoolParams`][arc.command.option.BoolParams]
- `int` & [`arc.IntParams`][arc.command.option.IntParams]
- `float` & [`arc.FloatParams`][arc.command.option.FloatParams]
- `str` & [`arc.StrParams`][arc.command.option.StrParams]
- `hikari.Attachment` & [`arc.AttachmentParams`][arc.command.option.AttachmentParams]
- `hikari.User` & [`arc.UserParams`][arc.command.option.UserParams]
- `hikari.Role` & [`arc.RoleParams`][arc.command.option.RoleParams]
- `hikari.User | hikari.Role` & [`arc.MentionableParams`][arc.command.option.MentionableParams]
- Any hikari channel type & [`arc.ChannelParams`][arc.command.option.ChannelParams]

Trying to use any other type as an option will lead to errors.

!!! tip
    The types of channels a user can pass to a **channel option** will depend on the type(s) of channels specified as the first parameter of a channel option.

    This will only allow textable guild channels to be passed:

    ```py
    textable: arc.Option[hikari.TextableGuildChannel, arc.ChannelParams(...)]
    ```

    And this will only allow news or text channels:

    ```py
    news_or_text: arc.Option[hikari.GuildTextChannel | hikari.GuildNewsChannel, arc.ChannelParams(...)]
    ```

    To allow any channel type (including categories and threads!) use `hikari.PartialChannel`.

## Autocomplete

`str`, `int` and `float` support autocomplete, which means that you can dynamically offer choices as the user is typing in their input.

First, you need to define an autocomplete callback, this will be called repeatedly as the user is typing in the option:

=== "Gateway"

    ```py
    async def provide_opts(data: arc.AutocompleteData[arc.GatewayClient, str]) -> list[str]:
        if data.focused_value and len(data.focused_value) > 20:
            return ["That", "is", "so", "long!"]
        return ["Short", "is", "better!"]
    ```

=== "REST"

    ```py
    async def provide_opts(data: arc.AutocompleteData[arc.RESTClient, str]) -> list[str]:
        if data.focused_value and len(data.focused_value) > 20:
            return ["That", "is", "so", "long!"]
        return ["Short", "is", "better!"]
    ```

This callback should either return a `list[option_type]` (`list[str]`) in this case, or a `list[hikari.CommandChoice]`.

Then, to add autocomplete to an option, specify the `autocomplete_with=` argument in the params object and pass your autocomplete callback:

=== "Gateway"

    ```py
    @client.include
    @arc.slash_command("autocomplete", "Autocomplete options!")
    async def autocomplete_command(
        ctx: arc.GatewayContext,
        # Set the 'autocomplete_with' parameter to the function that will be used to autocomplete the option
        complete_me: arc.Option[str, arc.StrParams(description="I'll complete you!", autocomplete_with=provide_opts)]
    ) -> None:
        await ctx.respond(f"You wrote: `{complete_me}`")
    ```

=== "REST"

    ```py
    @client.include
    @arc.slash_command("autocomplete", "Autocomplete options!")
    async def autocomplete_command(
        ctx: arc.RESTContext,
        # Set the 'autocomplete_with' parameter to the function that will be used to autocomplete the option
        complete_me: arc.Option[str, arc.StrParams(description="I'll complete you!", autocomplete_with=provide_opts)]
    ) -> None:
        await ctx.respond(f"You wrote: `{complete_me}`")
    ```

With the following example, the autocompletion suggestions should change as your input reaches 20 characters.
