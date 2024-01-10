---
title: Context Menu Commands
description: A guide on defining commands inside context menus
hide:
  - toc
---

# Context Menu Commands

<figure markdown>
  ![Context Menu Commands](../assets/context_menu.png){ width="600" .no-lightbox }
  <figcaption>An example context menu command</figcaption>
</figure>

Commands can also be defined in **context menus** that appear when you right-click a user or message. These commands have some limitations:

- Options are not supported
- Subcommands and groups are not supported
- There is a **maximum** of 5 user commands and 5 message commands a bot can have

Additionally, context-menu commands do not have the same naming limitations as slash commands,
their names can contain spaces and uppercase letters.

To define a user command, use [`@arc.user_command`][arc.command.user.user_command]:

=== "Gateway"

    ```py
    @client.include
    @arc.user_command("Say Hi")
    async def hi_user(ctx: arc.GatewayContext, user: hikari.User) -> None:
        await ctx.respond(f"Hey {user.mention}!")
    ```

=== "REST"

    ```py
    @client.include
    @arc.user_command("Say Hi")
    async def hi_user(ctx: arc.RESTContext, user: hikari.User) -> None:
        await ctx.respond(f"Hey {user.mention}!")
    ```

To define a message command, use [`@arc.message_command`][arc.command.message.message_command]:

=== "Gateway"

    ```py
    @client.include
    @arc.message_command("Say Hi")
    async def hi_message(ctx: arc.GatewayContext, message: hikari.Message) -> None:
        await ctx.respond(f"Hey {message.author.mention}!")
    ```

=== "REST"

    ```py
    @client.include
    @arc.message_command("Say Hi")
    async def hi_message(ctx: arc.RESTContext, message: hikari.Message) -> None:
        await ctx.respond(f"Hey {message.author.mention}!")
    ```

The second argument of a context-menu command will always be the target of the command (the message/user that was right-clicked).
