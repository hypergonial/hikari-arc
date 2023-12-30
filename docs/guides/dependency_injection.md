---
title: Dependency Injection
description: A guide on dependency injection & arc
---

# Dependency Injection

**Dependency Injection** is a programming pattern aimed at seperating the initialization of state from functions that need to perform operations on said state. For example, if you have a function that needs access to a database, we can *inject* the database to said function when it is called. In the case of Discord bots, it can be a good way to share state, such as access to a database, an http client and so on.

`arc` uses [`alluka`](https://alluka.cursed.solutions/usage/) to facilitate dependency injection, and command callbacks are automatically injected with declared dependencies.

## Setting dependencies

=== "Gateway"

    ```py
    import typing

    import hikari
    import arc

    # This is just an example "database" that stores a single integer
    class MyDatabase:
        def __init__(self, value: int) -> None:
            self.value = value

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)


    database = MyDatabase(value=0)

    # We declare a new dependency of type 'MyDatabase' and the value of 'database'
    client.set_type_dependency(MyDatabase, database)
    ```

=== "REST"

    ```py
    import typing

    import hikari
    import arc

    # This is just an example "database" that stores a single integer
    class MyDatabase:
        def __init__(self, value: int) -> None:
            self.value = value

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)


    database = MyDatabase(value=0)

    # We declare a new dependency of type 'MyDatabase' and the value of 'database'
    client.set_type_dependency(MyDatabase, database)
    ```

In the above example, we asked `arc` that every time we ask for a dependency of type `MyDatabase`, it should return the specific instance we gave it as the second parameter to [`Client.set_type_dependency`][arc.client.Client.set_type_dependency]

## Injecting dependencies

=== "Gateway"

    ```py
    @client.include
    @arc.slash_command("increment", "Increment a counter!")
    # We inject a dependency of type 'MyDatabase' here.
    async def increment(
        ctx: arc.Context[arc.GatewayClient],
        db: MyDatabase = arc.inject()
    ) -> None:
        db.value += 1
        await ctx.respond(f"Counter is at: `{db.value}`")

    ```

=== "REST"

    ```py
    @client.include
    @arc.slash_command("increment", "Increment a counter!")
    # We inject a dependency of type 'MyDatabase' here.
    async def increment(
        ctx: arc.Context[arc.RESTClient],
        db: MyDatabase = arc.inject()
    ) -> None:
        db.value += 1
        await ctx.respond(f"Counter is at: `{db.value}`")

    ```

And here we request that `arc` injects the dependency we declared earlier into our command, passing the "database" to it. If you combine this example with the prior one, you should get a command that increments a counter every time it is invoked, and prints it's current state.

### Injecting other functions

By default, only command callbacks are injected with dependencies, but you might want to inject other functions too. This can be done via the [`@Client.inject_dependencies`][arc.client.Client.inject_dependencies] decorator (or [`@Plugin.inject_dependencies`][arc.plugin.Plugin.inject_dependencies] if working in a plugin).

```py
@client.inject_dependencies
def compare_counter(value: int, db: MyDatabase = arc.inject()) -> None:
    if value > db.value:
        print("Value is bigger!")
    else:
        print("Counter is bigger or equal!")
```

!!! warning
    Trying to use [`arc.inject()`][alluka.inject] outside a command or a function decorated with [`@Client.inject_dependencies`][arc.client.Client.inject_dependencies] will lead to unexpected results.

## The benefits of dependency injection

Dependency injection **separates the concern** of constructing an object from using them, therefore it is possible to **loosely couple** the logic and state of your program. One benefit of this approach is that we can separate the actual implementations from the abstract types that functions may consume.

!!! tip
    If you do not know what [ABC](https://docs.python.org/3/glossary.html#term-abstract-base-class "Abstract Base Class")s in Python are, it is recommended that you [familiarize yourself](https://docs.python.org/3/library/abc.html) with them first before following this guide further.

```py
import abc

# Abstract base type for a database of some kind
class Database(abc.ABC):

    @abc.abstractmethod
    async def fetch_data(self) -> int:
        ...

# "Real" database
class ProductionDatabase(Database):

    async def fetch_data(self) -> int:
        # Fetch data from a supposed "database"
        return 10

# Testing database
class MockDatabase(Database):

    async def fetch_data(self) -> int:
        # Return "fake" testing data
        return 0
```

Let's say our app has two configurations, a "testing mode" where we want our "database" to simply return fake values, and a "production mode" where it actually connects to a real database and fetches values from it. If your code relies on the concrete implementation of `ProductionDatabase` or `MockDatabase`, it is hard to switch it out on the fly, however if your code only depends on `Database`, you can effectively swap out which underlying implementation of `Database` it is using, and your code continues to work!

=== "Gateway"

    ```py
    is_testing = True # Change me!

    client = arc.GatewayClient(...)

    if is_testing:
        client.set_type_dependency(Database, MockDatabase())
    else:
        client.set_type_dependency(Database, ProductionDatabase())

    @client.include
    @arc.slash_command("fetch", "Fetch totally real data some of the time!")
    # We inject 'Database' here, the caller doesn't know which
    # implementation it will get!
    async def fetch_data(
        ctx: arc.Context[arc.GatewayClient],
        db: Database = arc.inject()
    ) -> None:
        data = await db.fetch_data()
        await ctx.respond(f"Data is: `{data}`")
    ```

=== "REST"

    ```py
    is_testing = True # Change me!

    client = arc.RESTClient(...)

    if is_testing:
        client.set_type_dependency(Database, MockDatabase())
    else:
        client.set_type_dependency(Database, ProductionDatabase())

    @client.include
    @arc.slash_command("fetch", "Fetch totally real data some of the time!")
    # We inject 'Database' here, the caller doesn't know which
    # implementation it will get!
    async def fetch_data(
        ctx: arc.Context[arc.RESTClient],
        db: Database = arc.inject()
    ) -> None:
        data = await db.fetch_data()
        await ctx.respond(f"Data is: `{data}`")
    ```

Try running the example with the `is_testing` variable set to both `True` and `False`, and see what happens! If everything is right, the command should respond with `0` if `is_testing` is `True`, otherwise `0`.

In a real scenario, this would allow you to effectively swap what database implementation your bot uses, as long as it conforms to the `Database` abstract type.
