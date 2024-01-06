import hikari

import arc

bot = hikari.GatewayBot("...")
# Set the locales that the client will request in the provider callbacks.
client = arc.GatewayClient(bot, provided_locales=[hikari.Locale.EN_US, hikari.Locale.ES_ES])

# These are just examples, you can provide localizations from anywhere you want.
COMMAND_LOCALES = {
    "hi": {
        hikari.Locale.EN_US: {"name": "hi", "description": "Say hi to someone!"},
        hikari.Locale.ES_ES: {"name": "hola", "description": "¡Saluda a alguien!"},
    }
}

OPTION_LOCALES = {
    "hi": {
        "user": {
            hikari.Locale.EN_US: {"name": "user", "description": "The user to say hi to."},
            hikari.Locale.ES_ES: {"name": "usuario", "description": "El usuario al que saludar."},
        }
    }
}

CUSTOM_LOCALES = {"say_hi": {hikari.Locale.EN_US: "Hey {user}!", hikari.Locale.ES_ES: "¡Hola {user}!"}}


# This callback will be called when a command needs to be localized.
# The request includes the command and the locale to be used.
@client.set_command_locale_provider
def command_locale_provider(request: arc.CommandLocaleRequest) -> arc.LocaleResponse:
    return arc.LocaleResponse(**COMMAND_LOCALES[request.name][request.locale])


# This callback will be called when an option needs to be localized.
# The request includes the option and the locale to be used.
@client.set_option_locale_provider
def option_locale_provider(request: arc.OptionLocaleRequest) -> arc.LocaleResponse:
    return arc.LocaleResponse(**OPTION_LOCALES[request.command.name][request.name][request.locale])


# This callback will be called for every 'ctx.loc()' call.
# The '.key' attribute is the string that is passed to the 'ctx.loc()' method.
@client.set_custom_locale_provider
def custom_locale_provider(request: arc.CustomLocaleRequest) -> str:
    return CUSTOM_LOCALES[request.key][request.locale]


@client.include
@arc.slash_command(name="hi", description="Say hi to someone!")
async def hi_slash(
    ctx: arc.GatewayContext, user: arc.Option[hikari.User, arc.UserParams("The user to say hi to.")]
) -> None:
    # ctx.loc can be used to request custom localizations that are not related to commands or options.
    # Additional keyword arguments passed to the method will be passed to .format()
    await ctx.respond(ctx.loc("say_hi", user=user.mention))


# Note: 'ctx.loc()' will by default request the guild's locale, outside of guilds it will request the user's locale.
# You can pass use_guild=False to always request the user's locale instead.


bot.run()
