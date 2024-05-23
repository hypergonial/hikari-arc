---
title: Startup & Shutdown
description: A guide on handling lifecycle in arc
hide:
  - toc
---

# Startup & Shutdown

It is possible to execute code when the client has started up or shut down, this can be done via the [`@Client.add_startup_hook`][arc.abc.Client.add_startup_hook] and [`@Client.add_shutdown_hook`][arc.abc.Client.add_shutdown_hook] respectively.

=== "Gateway"

    ```py
    @client.add_startup_hook
    async def startup_hook(client: arc.GatewayClient) -> None:
        print("Client started up!")
    ```

=== "REST"

    ```py
    @client.add_startup_hook
    async def startup_hook(client: arc.RESTClient) -> None:
        print("Client started up!")
    ```

The **startup hook** is a great place to initialize resources that require an async context and/or the bot to be started. It is called after the client has already synced all commands and the underlying bot has fully started.

=== "Gateway"

    ```py
    @client.add_shutdown_hook
    async def shutdown_hook(client: arc.GatewayClient) -> None:
        print("Client shut down!")
    ```

=== "REST"

    ```py
    @client.add_shutdown_hook
    async def shutdown_hook(client: arc.RESTClient) -> None:
        print("Client shut down!")
    ```

The **shutdown hook** is where you can clean up any remaining resources, close connections, etc. It is called when the bot has started to shut down.

## Lifecycle Events

!!! info "Gateway only"
    This section is only relevant to those using a **Gateway** client, as REST bots **cannot receive events**.

If you prefer handling your client's lifecycle via [events](./events.md), you may listen for [`arc.StartedEvent`][arc.events.StartedEvent] or [`arc.StoppingEvent`][arc.events.StoppingEvent] respectively. These are dispatched immediately after the lifecycle hooks were processed, guaranteeing that the client is in the right state.

```py
@client.listen()
async def on_startup(event: arc.StartedEvent) -> None:
    print("Client started up!")
```

!!! question "What is the difference between `arc.StartedEvent` and `hikari.StartedEvent`?"
    `arc.StartedEvent` fires after the client has already synced all commands and initialized internally, which happens *after* `hikari.StartedEvent` fires, therefore it is the recommended to use `arc.StartedEvent` over `hikari.StartedEvent`.
