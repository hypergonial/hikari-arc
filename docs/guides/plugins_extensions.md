---
title: Plugins & Extensions
description: A guide on plugins & extensions in arc
---

# Plugins & Extensions

## Plugins

Plugins are a way to group commands and related functionality together. This can then be combined with [extensions](#extensions) to allow for easy code modularization.

```py

plugin = GatewayPlugin("plugin name")

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

In the snippet above, we define a new plugin, add two commands to it, then add the plugin to the client. This in turn adds all commands added to the plugin to the client as well. Plugins can also have [hooks](./hooks.md) added to them, which will be used for every command added to the plugin. Additionally, it is possible to set an [error handler](./error_handling.md) on a plugin.

!!! note
    Anything that can be used with `@client.include` can also be used with `@plugin.include` as well.

## Extensions

Extensions allow `arc` to load additional modules and pass your client instance to them. They can be loaded & unloaded dynamically during runtime. An extension is valid from `arc`'s perspective if it has a function decorated with [`@arc.loader`][arc.extension.loader]. A loader function should take a client as it's sole parameter. You may optionally also define an [`@arc.unloader`][arc.extension.unloader] function, however keep in mind if that no unloader is defined, the extension cannot be unloaded.

!!! note
    It is **not** required to use plugins in conjunction with extensions, the two features can be used seperately, however it is *recommended* for simplicity's sake to make one extension contain one plugin.

Let's suppose we have the following folder structure:

```
bot.py
extensions
├── bar.py
└── foo.py
```

=== "Gateway"

    `foo.py`:

    ```py
    import arc

    plugin = arc.GatewayPlugin("foo")

    @plugin.include
    @arc.slash_command("foo", "Foo command")
    async def foo_cmd(
        ctx: arc.GatewayContext,
    ) -> None:
        await ctx.respond(f"Foo!")

    @arc.loader
    def loader(client: arc.GatewayClient) -> None:
        client.add_plugin(plugin)


    @arc.unloader
    def unloader(client: arc.GatewayClient) -> None:
        client.remove_plugin(plugin)
    ```

    `bar.py`:

    ```py
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

    `foo.py`:

    ```py
    import arc

    plugin = arc.RESTPlugin("foo")

    @plugin.include
    @arc.slash_command("foo", "Foo command")
    async def foo_cmd(
        ctx: arc.RESTContext,
    ) -> None:
        await ctx.respond(f"Foo!")

    # ...

    @arc.loader
    def loader(client: arc.RESTClient) -> None:
        client.add_plugin(plugin)


    @arc.unloader
    def unloader(client: arc.RESTClient) -> None:
        client.remove_plugin(plugin)
    ```

    `bar.py`:

    ```py
    import arc

    plugin = arc.RESTPlugin("bar")

    @plugin.include
    @arc.slash_command("bar", "Bar command")
    async def bar_cmd(
        ctx: arc.RESTContext,
    ) -> None:
        await ctx.respond(f"Bar!")

    # ...

    @arc.loader
    def loader(client: arc.RESTClient) -> None:
        client.add_plugin(plugin)


    @arc.unloader
    def unloader(client: arc.RESTClient) -> None:
        client.remove_plugin(plugin)
    ```

To load `foo.py` into the client before execution, you can use [`Client.load_extension`][arc.abc.client.Client.load_extension]

=== "Gateway"

    ```py
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)

    client.load_extension("extensions.foo")


    bot.run()
    ```

=== "REST"

    ```py
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)

    client.load_extension("extensions.foo")


    bot.run()
    ```

Or to load all extensions from the `extensions` folder, you can use [`Client.load_extensions_from`][arc.abc.client.Client.load_extensions_from]:

=== "Gateway"

    ```py
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)

    # Will run foo.loader()
    client.load_extensions_from("extensions")


    bot.run()
    ```

=== "REST"

    ```py
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)

    # Will run foo.loader() and bar.loader()
    client.load_extensions_from("extensions")


    bot.run()
    ```
