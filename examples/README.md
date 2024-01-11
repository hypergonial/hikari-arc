# Examples

Welcome to the examples! The aim of these short snippets of code are to demonstrate some example usecases on how to use arc, and showcase the numerous features of the library.

## Running examples

To run and test the examples, simply insert your token in into the constructor of `hikari.GatewayBot(...)`/`hikari.RESTBot(...)` by replacing the `...`, then run the example using the following command:

```sh
python example_name.py
```

If you have any questions, or found an issue with one of the examples, feel free to [open an issue](https://github.com/hypergonial/hikari-arc/issues/new/choose), or join the [hikari discord](https://discord.gg/hikari)!

## Gateway or REST?

> [!TIP]
> If you're unsure which one to choose, it is recommended that you get started with a **Gateway bot**.

There are two main ways for a bot to connect to Discord & receive [interactions](https://arc.hypergonial.com/guides/interactions/), via either a **GatewayBot** or a **RESTBot**.

A bot connected to the [**Gateway**](https://discord.com/developers/docs/topics/gateway) needs to maintain a constant connection to Discord's servers through a [WebSocket](https://en.wikipedia.org/wiki/WebSocket),
and in turn receives [**events**](https://arc.hypergonial.com/guides/events/) that inform it about things happening on Discord in real time (messages being sent, channels being created etc...).
[**Interactions**](https://arc.hypergonial.com/guides/interactions/) are also delivered to a bot of this type through the Gateway as events. In addition, Gateway bots typically have a [*cache*](https://arc.hypergonial.com/api_reference/client/#arc.client.GatewayClientBase.cache) and can manage complex state.
This model is ideal for bots that need to do things other than just responding to slash commands, such as reading and responding to messages sent by users, or acting on other server events (e.g. a moderation bot).

A **RESTBot** however, isn't constantly connected to Discord, instead, you're expected to host a small HTTP server, and Discord will send [interactions](https://arc.hypergonial.com/guides/interactions/) to your server
by making HTTP `POST` requests to it. RESTBots **only receive [interactions](https://arc.hypergonial.com/guides/interactions/)** from Discord, they **do not receive events** or other types of data. They are ideal for bots that manage little to no state,
and rely only on users invoking the bot via slash commands. Setting up a RESTBot however is slightly more complicated compared to a GatewayBot, as it requires a publically accessible [domain](https://en.wikipedia.org/wiki/Domain_name) with [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security) for Discord to be able to send interactions to your webserver.

> **Does this mean a Gateway bot cannot use the REST API?**
>
> **No.** Both Gateway & REST bots have access to the HTTP REST API Discord provides (see [`Client.rest`](https://arc.hypergonial.com/api_reference/abc/client/#arc.abc.client.Client.rest)), the primary difference between the two bot types is how Discord communicates with **your bot**, and what information it sends to it.
