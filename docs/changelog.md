---
title: Changelogs
description: All changelogs for hikari-arc
hide:
  - navigation
---

# Changelogs

Here you can find all the changelogs for `hikari-arc`.

## Unreleased

- Add `Client.create_task` to make it easier to create "fire and forget" tasks.
- Add `Client.is_started` and `Client.wait_until_started` for more convenient lifecycle management.
- Add the ability to pass an already existing injector instance to `Client` via the `injector=` kwarg. If not passed, a new injector will be created by default, like before.
- Set the client as a type dependency upon instantiation.
- Stabilize `Context.issued_response`. This property returns a boolean that is `True` if the underlying interaction has already received an initial response.
- Fix edgecase where options defaulted to `None` would be ignored in Python 3.10.
- Make usage of `__slots__` consistent across the library.

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
