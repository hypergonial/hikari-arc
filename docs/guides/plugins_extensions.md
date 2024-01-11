---
title: Plugins & Extensions
description: A guide on plugins & extensions in arc
hide:
  - toc
---

# Plugins & Extensions

## Plugins

Plugins are a way to group commands and related functionality together. This can then be combined with [extensions](#extensions) to allow for easy code modularization.

=== "Gateway"

    ```py hl_lines="1 3 8"
    plugin = arc.GatewayPlugin("plugin name")

    @plugin.include
    @arc.slash_command("name", "description")
    async def plugin_cmd(ctx: arc.GatewayContext) -> None:
        ...

    @plugin.include
    @arc.slash_command("other-name", "description")
    async def other_plugin_cmd(ctx: arc.GatewayContext) -> None:
        ...

    client.add_plugin(plugin)
    ```

=== "REST"

    ```py hl_lines="1 3 8"
    plugin = arc.RESTPlugin("plugin name")

    @plugin.include
    @arc.slash_command("name", "description")
    async def plugin_cmd(ctx: arc.RESTContext) -> None:
        ...

    @plugin.include
    @arc.slash_command("other-name", "description")
    async def other_plugin_cmd(ctx: arc.RESTContext) -> None:
        ...

    client.add_plugin(plugin)
    ```

In the snippet above, we define a new plugin, add two commands to it, then add the plugin to the client. This in turn adds all commands added to the plugin to the client as well.

!!! tip
    Anything that can be used with `@client.include` can also be used with `@plugin.include` as well. Plugins also define methods commonly found on the client such as [.include_slash_group()][arc.abc.PluginBase.include_slash_group] or [.walk_commands()][arc.abc.PluginBase.walk_commands].

The benefit of grouping commands together into a plugin is that you can define custom behaviour at the plugin level which applies to all commands added to the plugin. [Hooks](./hooks.md), [error handling](./error_handling.md), [concurrency limiting](./concurrency_limiting.md) and more can all be added to the plugin itself, additionally, you can also set attributes such as `autodefer=` or `default_permissions=`, and they will be applied to all commands that belong to the plugin.

For example, to make all commands in a plugin require `MANAGE_GUILD` permissions by default, you may use the following snippet:

=== "Gateway"

    ```py
    plugin = arc.GatewayPlugin("plugin name", default_permissions=hikari.Permissions.MANAGE_GUILD)
    ```

=== "REST"

    ```py
    plugin = arc.RESTPlugin("plugin name", default_permissions=hikari.Permissions.MANAGE_GUILD)
    ```

## Extensions

Extensions allow `arc` to load additional modules and pass your client instance to them. They can be loaded & unloaded dynamically during runtime. An extension is valid from `arc`'s perspective if it has a function decorated with [`@arc.loader`][arc.extension.loader]. A loader function should take a client as it's sole parameter. You may optionally also define an [`@arc.unloader`][arc.extension.unloader] function, however keep in mind if that no unloader is defined, the extension cannot be unloaded.

!!! note
    It is **not** required to use plugins in conjunction with extensions, the two features can be used seperately, however it is *recommended* for simplicity's sake to make one extension contain one plugin.

Let's suppose you have the following folder structure:

```
bot.py
extensions
├── bar.py
└── foo.py
```

=== "Gateway"

    ```py title="extensions/foo.py"
    import arc

    plugin = arc.GatewayPlugin("foo")

    @plugin.include
    @arc.slash_command("foo", "Foo command")
    async def foo_cmd(
        ctx: arc.GatewayContext,
    ) -> None:
        await ctx.respond(f"Foo!")

    # This will run when the extension is loaded
    # If there is no loader, the extension cannot be loaded!
    @arc.loader
    def loader(client: arc.GatewayClient) -> None:
        client.add_plugin(plugin)

    # If you add an unloader, the extension can also be unloaded at runtime!
    # Adding an unloader is optional.
    @arc.unloader
    def unloader(client: arc.GatewayClient) -> None:
        client.remove_plugin(plugin)
    ```

    ```py title="extensions/bar.py"
    import arc

    plugin = arc.GatewayPlugin("bar")

    @plugin.include
    @arc.slash_command("bar", "Bar command")
    async def bar_cmd(
        ctx: arc.GatewayContext,
    ) -> None:
        await ctx.respond(f"Bar!")

    @arc.loader
    def loader(client: arc.GatewayClient) -> None:
        client.add_plugin(plugin)


    @arc.unloader
    def unloader(client: arc.GatewayClient) -> None:
        client.remove_plugin(plugin)
    ```

=== "REST"

    ```py title="extensions/foo.py"
    import arc

    plugin = arc.RESTPlugin("foo")

    @plugin.include
    @arc.slash_command("foo", "Foo command")
    async def foo_cmd(
        ctx: arc.RESTContext,
    ) -> None:
        await ctx.respond(f"Foo!")

    # This will run when the extension is loaded
    # If there is no loader, the extension cannot be loaded!
    @arc.loader
    def loader(client: arc.RESTClient) -> None:
        client.add_plugin(plugin)

    # If you add an unloader, the extension can also be unloaded at runtime!
    # Adding an unloader is optional.
    @arc.unloader
    def unloader(client: arc.RESTClient) -> None:
        client.remove_plugin(plugin)
    ```

    ```py title="extensions/bar.py"
    import arc

    plugin = arc.RESTPlugin("bar")

    @plugin.include
    @arc.slash_command("bar", "Bar command")
    async def bar_cmd(
        ctx: arc.RESTContext,
    ) -> None:
        await ctx.respond(f"Bar!")

    @arc.loader
    def loader(client: arc.RESTClient) -> None:
        client.add_plugin(plugin)


    @arc.unloader
    def unloader(client: arc.RESTClient) -> None:
        client.remove_plugin(plugin)
    ```

To load `foo.py` into the client before execution, you can use [`Client.load_extension`][arc.abc.client.Client.load_extension]

=== "Gateway"

    ```py title="bot.py" hl_lines="7 8"
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)

    # Will run foo.loader()
    client.load_extension("extensions.foo")


    bot.run()
    ```

=== "REST"

    ```py title="bot.py" hl_lines="7 8"
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)

    # Will run foo.loader()
    client.load_extension("extensions.foo")


    bot.run()
    ```

Or to load all extensions from the `extensions` folder, you can use [`Client.load_extensions_from`][arc.abc.client.Client.load_extensions_from]:

=== "Gateway"

    ```py title="bot.py" hl_lines="7 8"
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)

    # Will run foo.loader() and bar.loader()
    client.load_extensions_from("extensions")


    bot.run()
    ```

=== "REST"

    ```py title="bot.py" hl_lines="7 8"
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)

    # Will run foo.loader() and bar.loader()
    client.load_extensions_from("extensions")


    bot.run()
    ```
