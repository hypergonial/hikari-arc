import hikari

import arc

# Extensions are a way to split your code into multiple files
# Related documentation guide: https://arc.hypergonial.com/guides/plugin_extensions

bot = hikari.GatewayBot("...")
client = arc.GatewayClient(bot)

# Load all extensions located in the 'extensions' directory
client.load_extensions_from("extensions")
# You can also use 'client.load_extension' to load a single extension.

bot.run()
