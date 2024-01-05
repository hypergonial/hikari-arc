import arc

# Plugins are a way to organize commands and other functionality
plugin = arc.GatewayPlugin("foo")


@plugin.include
@arc.slash_command("foo", "Foo command")
async def foo_cmd(ctx: arc.GatewayContext) -> None:
    await ctx.respond("Foo!")


# This will be called when the extension is loaded
# A loader must be present for the extension to be valid
@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)


# And this will be called when the extension is unloaded
# Including this is optional, but if not present, the extension cannot be unloaded
@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
