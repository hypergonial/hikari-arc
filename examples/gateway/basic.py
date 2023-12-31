import hikari
import arc

bot = hikari.GatewayBot("TOKEN")
client = arc.GatewayClient(bot)


@client.include
@arc.slash_command(name="hi", description="Say hi to someone!")
async def hi_slash(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
) -> None:
    await ctx.respond(f"Hey {user.mention}!")

bot.run()
