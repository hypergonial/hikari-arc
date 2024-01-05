import arc

# Plugins are a way to organize commands and other functionality
plugin = arc.RESTPlugin("bar")


@plugin.include
@arc.slash_command("bar", "Bar command")
async def bar_cmd(ctx: arc.RESTContext) -> None:
    await ctx.respond("Bar!")


# This will be called when the extension is loaded
# A loader must be present for the extension to be valid
@arc.loader
def loader(client: arc.RESTClient) -> None:
    client.add_plugin(plugin)


# And this will be called when the extension is unloaded
# Including this is optional, but if not present, the extension cannot be unloaded
@arc.unloader
def unloader(client: arc.RESTClient) -> None:
    client.remove_plugin(plugin)
