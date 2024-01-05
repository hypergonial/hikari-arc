import hikari

import arc


# Define a custom bot class that extends hikari.RESTBot
# Note that this is not strictly required, but is possible
class MyBot(hikari.RESTBot):
    def custom_method(self) -> str:
        return "I'm doing stuff!"


# You should inherit from arc.RESTClientBase
# and specify the bot class that your client will use
# If you do not have a custom bot class, you can use hikari.RESTBot here
class MyClient(arc.RESTClientBase[MyBot]):
    def custom_client_method(self) -> None:
        print(self.app.custom_method())


# Optional but recommended:
# Create type aliases for your context and plugin types
MyContext = arc.Context[MyClient]
MyPlugin = arc.RESTPluginBase[MyClient]

# Create your bot instance and client instance
bot = MyBot("...", banner=None)
client = MyClient(bot)


# Use in commands like normal
@client.include()
@arc.slash_command("test", "My command description")
async def my_command(ctx: MyContext) -> None:
    ctx.client.custom_client_method()
    await ctx.respond(ctx.client.app.custom_method())


bot.run()
