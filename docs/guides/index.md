---
title: Guides
description: Guides on how to use arc, and how app commands work on Discord
hide:
  - toc
---

# Guides

In this section you can find various in-depth guides that explain specific topics in detail. There's also fully functional [examples](https://github.com/hypergonial/hikari-arc/tree/main/examples) in the repository, if you prefer to learn that way.

If you think something is missing or inaccurate, please [open an issue](https://github.com/hypergonial/hikari-arc/issues/new/choose)!

<div class="grid cards" markdown>

-   :material-language-python:{ .lg .middle } **Typing & Type Hints**

    ---

    `arc` uses type-hints & typing extensively, so if you need
    a refresher on what they are, and how to use them, start here!

    [:octicons-arrow-right-24: Learn more](./typing.md)

-   :material-white-balance-sunny:{ .lg .middle } **Hikari Fundamentals**

    ---

    Learn the basics of how to use `hikari`, the foundation upon
    which `arc` builds.

    [:octicons-arrow-right-24: Learn more](./hikari_fundamentals.md)

-   :material-api:{ .lg .middle } **Interactions**

    ---

    Learn how app commands work under the hood, and
    what you can do with them!

    [:octicons-arrow-right-24: Learn more](./interactions.md)

-   :material-slash-forward:{ .lg .middle } **Options**

    ---

    Add options to your slash commands to get user input,
    set constraints, autocomplete, and more!

    [:octicons-arrow-right-24: Learn more](./options.md)

-   :material-folder-open:{ .lg .middle } **Command Groups**

    ---

    Group your commands into command groups and subgroups,
    nest subcommands to create a cohesive experience!

    [:octicons-arrow-right-24: Learn more](./command_groups.md)

-   :material-menu:{ .lg .middle } **Context Menus**

    ---

    Add commands directly to right-click context menus via
    user and message commands!

    [:octicons-arrow-right-24: Learn more](./context_menu.md)

-   :octicons-download-16:{ .lg .middle } **Installation & Invocation**

    ---

    Learn how you can make your commands installable by
    guilds and users alike, and how you can query this information at runtime!

    [:octicons-arrow-right-24: Learn more](./installation_contexts.md)

-   :material-power:{ .lg .middle } **Startup & Shutdown**

    ---

    Manage the lifecycle of your client using startup and
    shutdown hooks!

    [:octicons-arrow-right-24: Learn more](./startup_shutdown.md)

-   :material-hook:{ .lg .middle } **Hooks**

    ---

    Execute arbitrary logic before or after a command was run,
    perform checks, add cooldowns & more!

    [:octicons-arrow-right-24: Learn more](./hooks.md)

-   :fontawesome-solid-fire-flame-curved:{ .lg .middle } **Error Handling**

    ---

    Handle errors on the command, plugin or client level with customizable
    error handlers!

    [:octicons-arrow-right-24: Learn more](./error_handling.md)

-   :material-note-plus:{ .lg .middle } **Plugins & Extensions**

    ---

    Group commands into plugins & learn how you can seperate
    your bot into multiple source files!

    [:octicons-arrow-right-24: Learn more](./plugins_extensions.md)

-   :fontawesome-solid-syringe:{ .lg .middle } **Dependency Injection**

    ---

    Manage state in a type-safe manner using **dependency injection**,
    allowing you to use external dependencies in your bot, like a database
    or http client!

    [:octicons-arrow-right-24: Learn more](./dependency_injection.md)

-   :fontawesome-solid-infinity:{ .lg .middle } **Loops**

    ---

    Repeatedly call functions with a specific interval or crontab,
    allowing you to schedule basic tasks.

    [:octicons-arrow-right-24: Learn more](./loops.md)

-   :material-wall:{ .lg .middle } **Limiting Concurrency**

    ---

    Prevent users from invoking your command while it is already running
    with customizable concurrency limiters!

    [:octicons-arrow-right-24: Learn more](./concurrency_limiting.md)

-   :material-message-alert:{ .lg .middle } **Events**

    ---

    Listen to, and handle events coming through the Discord
    **Gateway**, such as message being sent, channels being created, & much more!

    [:octicons-arrow-right-24: Learn more](./events.md)

</div>
