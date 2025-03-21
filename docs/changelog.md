---
title: Changelogs
description: All changelogs for hikari-arc
hide:
  - navigation
---

# Changelogs

Here you can find all the changelogs for `hikari-arc`.

## 2.0.0

- **Breaking:** Remove `is_dm_enabled` from all command, plugin, and client types. Use the newly added `invocation_contexts` instead.
- **Breaking:** Remove deprecated `Client.set_startup_hook` and `Client.set_shutdown_hook`. Use the newly added `Client.add_startup_hook` and `Client.add_shutdown_hook` instead.
- **Breaking:** Remove `Context.get_channel` and `AutocompleteData.get_channel`. Use the newly added `Context.channel` and `AutocompleteData.channel` properties instead.
- Add support for **user installations** of commands.
  - Add `invocation_contexts` and `integration_types` to all command, plugin, and client types.
  - Add `invocation_context` and `authorizing_integration_owners` to `Context` and `AutocompleteData`.
- Add `Client.find_command` and `PluginBase.find_command` to get a command by name.
- Bump `hikari` to `v2.2.0`.

### Migration guide

#### `is_dm_enabled` removal

```py
# Before 2.0
client = arc.GatewayClient(..., is_dm_enabled=False)

# After 2.0

# Omit hikari.ApplicationContextType.BOT_DM to disable DMs
# You may also want to remove PRIVATE_CHANNEL if you don't want to support group DMs
client = arc.GatewayClient(
    ...,
    invocation_contexts=[
        hikari.ApplicationContextType.GUILD,
        hikari.ApplicationContextType.PRIVATE_CHANNEL
    ]
)
```

This applies similarly to command or plugin-level use of this setting.

#### `set_startup_hook` and `set_shutdown_hook` removal

```py
# Before 2.0

@client.set_startup_hook
async def startup_hook(client: arc.GatewayClient) -> None:
    print("Client started up!")

@client.set_shutdown_hook
async def shutdown_hook(client: arc.GatewayClient) -> None:
    print("Client shut down!")

# After 2.0

@client.add_startup_hook
async def startup_hook(client: arc.GatewayClient) -> None:
    print("Client started up!")

@client.add_shutdown_hook
async def shutdown_hook(client: arc.GatewayClient) -> None:
    print("Client shut down!")
```

#### `get_channel` removal

```py

# Before 2.0

@arc.slash_command("test", "Test command")
async def test(ctx: arc.GatewayContext) -> None:
    channel = ctx.get_channel()

# After 2.0

@arc.slash_command("test", "Test command")
async def test(ctx: arc.GatewayContext) -> None:
    channel = ctx.channel
```


## 1.4.0

- Add new optiontype with converter for `hikari.Emoji`.
- Work around `hikari` bug to solve command sync failing when a command has localizations.
- Bump `hikari` to `v2.0.0`.
- Add Python 3.13 support.

## v1.3.4

- Fix included basic hooks not working due to signature parsing.

## v1.3.3

- Fix hooks defined as async callable classes not working. (For instance, limiters)

## v1.3.2

- Add `IntervalLoop.set_interval()` to change the loop interval after loop creation.
- Fix error handling with slash subcommands sometimes causing infinite recursion.

## v1.3.1

- Add the ability to configure if an `IntervalLoop` should run immediately after being started or not.
- Fix `CronLoop` running immediately after being started.

## v1.3.0

- **Deprecate** `Client.set_startup_hook` and `Client.set_shutdown_hook`. These will be removed in `v2.0.0`. Use the newly added `Client.add_startup_hook` and `Client.add_shutdown_hook` instead.
- Add options with converters. These options do not exist on Discord's end, arc simply tries to convert a more primitive optiontype into the requested one, failing if it is not possible.
- Add new optiontypes with converters for `hikari.Member` and `hikari.Color`.
- Add `arc.OptionConverterFailureError` when a converter fails to convert an option value.
- Add support for injecting dependencies contextually to command callbacks, hooks, and error handlers via `Client.add_injection_hook` and `Client.remove_injection_hook`.
- Add support for multiple startup & shutdown hooks via `Client.add_startup_hook` and `Client.add_shutdown_hook` respectively.
- Inject dependencies by default into pre/post-execution hooks & error handlers.
- Fix client hooks being executed twice if a command is added to a plugin.
- Fix options mapping not taking name overrides into account.
- Bump alluka to `0.3+`.

## v1.2.1

- Fix `arc.utils.global_concurrency` missing a `limit` argument.
- Fix slash subcommands failing to resolve autodefer settings.

## v1.2.0

- Optimize command syncing by using bulk endpoints for global app commands as well, making it much faster.
- Improve command syncing error messages.
- Fix `@Client.listen` and `@Plugin.listen` failing to parse event types with generics from function signatures.

## v1.1.0

- Add `Client.create_task` to make it easier to create "fire and forget" tasks.
- Add `Client.is_started` and `Client.wait_until_started` for more convenient lifecycle management.
- Add the ability to pass an already existing injector instance to `Client` via the `injector=` kwarg. If not passed, a new injector will be created by default, like before.
- Set the client as a type dependency upon instantiation.
- Stabilize `Context.issued_response`. This property returns a boolean that is `True` if the underlying interaction has already received an initial response.
- Fix `hikari.User | hikari.Role | None` not being parsed as mentionable option.
- Fix edgecase where options defaulted to `None` would be ignored in Python 3.10.

## v1.0.0

This marks the **first stable release** of `arc`, meaning that from this point on, the project follows [semantic versioning](https://semver.org/), and no breaking changes will happen (until an eventual 2.0).

- Add [loops](./guides/loops.md). Loops can be used to repeatedly call a given coroutine function with a specific interval or cron set.
- Add [concurrency limiters](./guides/concurrency_limiting.md). Concurrency limiters can be used to prevent users from invoking a command that already has a specific amount of instances running.
- Add `arc.StartedEvent` and `arc.StoppingEvent` to gateway clients to enable managing lifecycle via events.
- Fix command groups always being republished when command syncing.

In additon to these changes, the [documentation](https://arc.hypergonial.com) got a major refresh, adding & extending guides where needed.

## v0.6.0

- Add `Context.get_option()` to access options outside the command callback in a type-safe manner.
- Add `Client.walk_commands()` and `Plugin.walk_commands()` to iterate over all commands & subcommands of a given type in a type-safe manner.
- Add `CallableCommandProto.display_name`, `SlashCommand.make_mention()`, `SlashSubCommand.make_mention()`.
- Change `Context.respond_with_builder()` to attempt a followup message when the interaction has an initial response and a message builder was passed.
- Remove the `acquire()` method from `LimiterProto` to make it easier to implement custom limiters.
- Split `arc.utils.hooks.RateLimiter` into `arc.utils.RateLimiter` and `arc.utils.hooks.LimiterHook`. This allows `arc.utils.RateLimiter` to be used independently of an arc context object.

## v0.5.0

- **Breaking:** Re-order OptionParams object parameters. `description=` is now the first & only positional argument. `name=` has been moved to the second parameter and is now keyword-only.
- Add [limiters](./guides/hooks.md#limiters).
- Add  `autodefer`, `default_permissions`, `is_dm_enabled` and `is_nsfw` to client & plugin types. If set, these settings will be applied to all commands added to the client/plugin. They can still however be overridden by individual commands.
- Add `GatewayClientBase` and `RESTClientBase` to aid in creating custom client types. Examples on how to do this have also been added to the repository.
- Fix `InteractionResponse.retrieve_message()` failing due to incorrect assertion.
- Fix subcommands & subgroups unable to have hooks or an error handler.

## v0.4.0

- Add localization support through locale providers. See the localization example for more.
- Add `@GatewayClient.listen`, `GatewayClient.subscribe`, `GatewayClient.unsubscribe`.
- Add `@GatewayPlugin.listen`, `GatewayPlugin.subscribe`, `GatewayPlugin.unsubscribe`.
- Make all first-order decorators work as second-order decorators as well.


## v0.3.0

- Add [hooks](./guides/hooks.md).
- Add lifecycle hooks to `Client` along with an error handler.
- Declare `attrs` explicitly as a dependency.

## v0.2.0

- **Breaking:** Rename `Context.edit_response()` to `Context.edit_initial_response()`. This is to make the purpose of the function clearer.
- **Breaking:** Remove `arc.Injected[T]` typehint alias. Use `arc.inject()` instead. This is to avoid confusion between the two.
- **Breaking:** Rename `GatewayPlugin` to `GatewayPluginBase` and `RESTPlugin` to `RESTPluginBase`.
- Add `GatewayContext` aliasing `Context[GatewayClient]`
- Add `RESTContext` aliasing `Context[RESTClient]`
- Add `GatewayPlugin` aliasing `GatewayPluginBase[GatewayClient]`
- Add `RESTPlugin` aliasing `RESTPlugin[RESTClient]`
- Add support for passing mappings to `choices=` when specifying option params.
- Move `ABC`s used internally under `arc.abc`.
- Improve handling missing responses via REST by adding `NoResponseIssuedError`.
- Fix `@plugin.inject_dependencies` failing when located outside of the main module.

## v0.1.3

- Fix `Context.respond_with_builder` issuing the response twice in REST.
- Do not export `abc`s to top-level.

## v0.1.2

- Add `Context.respond_with_modal`
- Add `BoolOption` and `BoolParams`
- Improve `Context.respond_with_builder` typing.

## v0.1.1

- Initial release
