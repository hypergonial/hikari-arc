---
title: Changelogs
description: All changelogs for hikari-arc
hide:
  - navigation
---

# Changelogs

Here you can find all the changelogs for `hikari-arc`.

<!--TODO: Remove arc.Injected[T] because it's confusing -->
## v0.1.4

- Add support for passing mappings to `choices=` when specifying option params.
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
