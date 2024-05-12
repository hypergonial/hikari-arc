---
title: Options
description: A guide on slash command options
hide:
  - toc
---

# Options

Options can be used to ask for user input in slash commands. They come in a variety of types and support various features, depending on the type.

!!! tip
    If you're not familiar with type-hinting in Python, you should read [this chapter](./typing.md) first.

## Declaring options

An **option** can be declared as parameters in the command callback using the following general syntax:

```py
var_name: arc.Option[something, arc.SomethingParams(...)]
```

Where `something` is a substitute for the type of the option.

This is what that looks like in action:

=== "Gateway"

    ```py hl_lines="5"
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.GatewayContext,
        number: arc.Option[int, arc.IntParams("A number")]
    ) -> None:
        await ctx.respond(f"You provided {number}!")
    ```

=== "REST"

    ```py hl_lines="5"
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.RESTContext,
        number: arc.Option[int, arc.IntParams("A number")]
    ) -> None:
        await ctx.respond(f"You provided {number}!")
    ```

To make an option **not required**, you should set a default value:

=== "Gateway"

    ```py hl_lines="5 6"
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.GatewayContext,
        number: arc.Option[int, arc.IntParams("A number")] = 10,
        user: arc.Option[hikari.User | None, arc.UserParams("A user")] = None,
    ) -> None:
        await ctx.respond(f"You provided {number} and {user.mention if user else None}!")
    ```

=== "REST"

    ```py hl_lines="5 6"
    @client.include
    @arc.slash_command("name", "description")
    async def options_cmd(
        ctx: arc.RESTContext,
        number: arc.Option[int, arc.IntParams("A number")] = 10,
        user: arc.Option[hikari.User | None, arc.UserParams("A user")] = None,
    ) -> None:
        await ctx.respond(f"You provided {number} and {user.mention if user else None}!")
    ```

### Basic option types

The following basic option types are supported:

| Type | Params object |
|------|---------------|
| `bool` | [`arc.BoolParams`][arc.command.option.BoolParams] |
| `int` | [`arc.IntParams`][arc.command.option.IntParams] |
| `float` | [`arc.FloatParams`][arc.command.option.FloatParams] |
| `str` | [`arc.StrParams`][arc.command.option.StrParams] |
| `hikari.Attachment` | [`arc.AttachmentParams`][arc.command.option.AttachmentParams] |
| `hikari.User` | [`arc.UserParams`][arc.command.option.UserParams] |
| `hikari.Role` | [`arc.RoleParams`][arc.command.option.RoleParams] |
| `hikari.User | hikari.Role` | [`arc.MentionableParams`][arc.command.option.MentionableParams] |
| Any hikari channel type | [`arc.ChannelParams`][arc.command.option.ChannelParams] |

These option types map directly to the ones [defined by the Discord API](https://discord.com/developers/docs/interactions/application-commands#application-command-object-application-command-option-type).

??? tip "Setting channel types"
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

### Option types with converters

`arc` also ships with a couple of custom option types not directly defined by the Discord API. These  use converters to try and convert from a more primitive option type:

| Type | Params object | Converts From |
|------|---------------|---------------|
| `hikari.Member` | [`arc.MemberParams`][arc.command.option.MemberParams] | `hikari.User` |
| `hikari.Color`  | [`arc.ColorParams`][arc.command.option.ColorParams]  | `str` |

If the option cannot be converted successfully, a [`OptionConverterFailureError`][arc.errors.OptionConverterFailureError] will be raised, and should be handled with an [error handler](./error_handling.md).

!!! warning
    Trying to use any other types from the ones listed above as an option will lead to errors.

## Choices & Autocomplete

`str`, `int` and `float` support setting **choices** or **autocomplete**, the latter of which means that you can dynamically offer choices as the user is typing in their input.

### Choices

Choices can be added to an option to define tell the user what values are valid. The choices will be shown as suggestions when the user has the option selected.

!!! warning
    If choices are present, they will be the **only valid** values for the option.

=== "Gateway"

    ```py hl_lines="6"
    @client.include
    @arc.slash_command("choices", "I can't choose!")
    async def choices_command(
        ctx: arc.GatewayContext,
        # Set the 'choices' parameter to all the valid values your option can be
        choose_me: arc.Option[int, arc.IntParams("Choose me!", choices=[1, 2, 3])]
    ) -> None:
        await ctx.respond(f"You wrote: `{choose_me}`")
    ```

=== "REST"

    ```py hl_lines="6"
    @client.include
    @arc.slash_command("choices", "I can't choose!")
    async def choices_command(
        ctx: arc.RESTContext,
        # Set the 'choices' parameter to all the valid values your option can be
        choose_me: arc.Option[int, arc.IntParams("Choose me!", choices=[1, 2, 3])]
    ) -> None:
        await ctx.respond(f"You wrote: `{choose_me}`")
    ```

You can also pass a mapping if you want to name your choices. Your command will receive the value, but your users will only see the names:

=== "Gateway"

    ```py hl_lines="6"
    @client.include
    @arc.slash_command("choices", "I can't choose!")
    async def choices_command(
        ctx: arc.GatewayContext,
        # Set the 'choices' parameter to all the valid values your option can be
        choose_me: arc.Option[int, arc.IntParams("Choose me!", choices={"one": 1, "two": 2, "three": 3})]
    ) -> None:
        await ctx.respond(f"You wrote: `{choose_me}`")
    ```

=== "REST"

    ```py hl_lines="6"
    @client.include
    @arc.slash_command("choices", "I can't choose!")
    async def choices_command(
        ctx: arc.RESTContext,
        # Set the 'choices' parameter to all the valid values your option can be
        choose_me: arc.Option[int, arc.IntParams("Choose me!", choices={"one": 1, "two": 2, "three": 3})]
    ) -> None:
        await ctx.respond(f"You wrote: `{choose_me}`")
    ```

!!! tip
    If you're simply looking to restrict the range of a numeric value or the length of a string, use the `min`/`max` or `min_length`/`max_length` parameters respectively.

### Autocomplete

Autocomplete is useful when you want to provide suggestions to the value of the option depending on what the user has typed, or even other option values if they have already been specified.

!!! warning
    Autocompleted options can still be **submitted with any value**, regardless of what values have been suggested to the user, unlike choices. You should validate your input.

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

This callback should return one of the following (where `ChoiceT` is the type of the option being autocompleted, e.g. `str`):

- `Sequence[ChoiceT]` to return a sequence of choices (e.g. `list[str]`)
- `Mapping[str, ChoiceT]` to return a mapping of names to values (e.g. `dict[str, str]`)
- `Sequence[hikari.impl.AutocompleteChoiceBuilder]` to also return a mapping of names to values along with localization


Then, to add autocomplete to an option, specify the `autocomplete_with=` argument in the params object and pass your autocomplete callback:

=== "Gateway"

    ```py hl_lines="6"
    @client.include
    @arc.slash_command("autocomplete", "Autocomplete options!")
    async def autocomplete_command(
        ctx: arc.GatewayContext,
        # Set the 'autocomplete_with' parameter to the function that will be used to autocomplete the option
        complete_me: arc.Option[str, arc.StrParams("I'll complete you!", autocomplete_with=provide_opts)]
    ) -> None:
        await ctx.respond(f"You wrote: `{complete_me}`")
    ```

=== "REST"

    ```py hl_lines="6"
    @client.include
    @arc.slash_command("autocomplete", "Autocomplete options!")
    async def autocomplete_command(
        ctx: arc.RESTContext,
        # Set the 'autocomplete_with' parameter to the function that will be used to autocomplete the option
        complete_me: arc.Option[str, arc.StrParams("I'll complete you!", autocomplete_with=provide_opts)]
    ) -> None:
        await ctx.respond(f"You wrote: `{complete_me}`")
    ```

With the following example, the autocompletion suggestions should change as your input reaches 20 characters.

!!! warning
    You cannot have `autocomplete_with=` and `choices=` defined at the same time.
