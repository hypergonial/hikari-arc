import hikari
import arc

bot = hikari.RESTBot("TOKEN")
client = arc.RESTClient(bot)


@client.include
@arc.slash_command(name="hi", description="Say hi to someone!")
async def hi_slash(
    ctx: arc.RESTContext,
    user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
) -> None:
    await ctx.respond(f"Hey {user.mention}!")

bot.run()
