---
title: Changelogs
description: All changelogs for hikari-arc
hide:
  - navigation
---

# Changelogs

Here you can find all the changelogs for `hikari-arc`.

## v0.5.0

- **Breaking:** Re-order OptionParams object parameters. `description=` is now the first & only positional argument. `name=` has been moved to the second parameter and is now keyword-only.
- Add [limiters](./guides/hooks.md#limiters).
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
