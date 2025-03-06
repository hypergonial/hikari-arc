---
title: Events
description: A guide on handling events in arc
hide:
  - toc
---

!!! info "Gateway only"
    This guide is only relevant to those using a **Gateway** client, as REST bots **cannot receive events**.

Your bot receives events based on what is happening in the guilds your bot is in, describing state changes (e.g. a new member joined, a message was sent) and allowing you to react to them. To make your bot react to a specific event, you must create a listener:

```py
# This only works with Gateway bots
bot = hikari.GatewayBot("...")
client = arc.GatewayClient(bot)

# ...

@client.listen()
async def on_message(event: hikari.MessageCreateEvent) -> None:

    # Ignore ourselves & other bots
    if not event.is_human:
        return

    await client.rest.create_message(event.channel_id, "Hi!")
```

With the above snippet, the bot will respond to *every* message sent with "Hi!".

Plugins can also have listeners, and behave similarly to those registered on the client itself:

```py
plugin = arc.GatewayPlugin("name")

# ...

@plugin.listen()
async def on_message(event: hikari.MessageCreateEvent) -> None:

    # Ignore ourselves & other bots
    if not event.is_human:
        return

    await plugin.client.rest.create_message(event.channel_id, "Hi!")
```

For a list of all available events, see the [hikari documentation](https://docs.hikari-py.dev/en/stable/reference/hikari/events/).
