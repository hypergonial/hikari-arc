---
title: Startup & Shutdown
description: A guide on handling lifecycle in arc
hide:
  - toc
---

# Startup & Shutdown

It is possible to execute code when the client has started up or shut down, this can be done via the [`@Client.set_startup_hook`][arc.abc.Client.set_startup_hook] and [`@Client.set_shutdown_hook`][arc.abc.Client.set_shutdown_hook] respectively.

=== "Gateway"

    ```py
    @client.set_startup_hook
    async def startup_hook(client: arc.GatewayClient) -> None:
        print("Client started up!")
    ```

=== "REST"

    ```py
    @client.set_startup_hook
    async def startup_hook(client: arc.RESTClient) -> None:
        print("Client started up!")
    ```

The **startup hook** is a great place to initialize resources that require an async context and/or the bot to be started. It is called after the client has already synced all commands and the underlying bot has fully started.

=== "Gateway"

    ```py
    @client.set_shutdown_hook
    async def shutdown_hook(client: arc.GatewayClient) -> None:
        print("Client shut down!")
    ```

=== "REST"

    ```py
    @client.set_shutdown_hook
    async def shutdown_hook(client: arc.RESTClient) -> None:
        print("Client shut down!")
    ```

The **shutdown hook** is where you can clean up any remaining resources, close connections, etc. It is called when the bot has started to shut down.
