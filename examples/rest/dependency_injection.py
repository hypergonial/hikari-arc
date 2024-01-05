import hikari

import arc

# arc uses dependency injection to manage state across commands
# Related documentation guide: https://arc.hypergonial.com/guides/dependency_injection


# This is just an example "database" that stores a single integer
class MyDatabase:
    def __init__(self, value: int) -> None:
        self.value = value


bot = hikari.RESTBot("...")
client = arc.RESTClient(bot)

# Create a new instance of 'MyDatabase'
database = MyDatabase(value=0)

# We declare a new dependency of type 'MyDatabase' and the value of 'database'
client.set_type_dependency(MyDatabase, database)


@client.include
@arc.slash_command("increment", "Increment a counter!")
# We inject a dependency of type 'MyDatabase' here.
async def increment(ctx: arc.RESTContext, db: MyDatabase = arc.inject()) -> None:
    db.value += 1
    await ctx.respond(f"Counter is at: `{db.value}`")


# You can also inject dependencies into functions that aren't commands
@client.inject_dependencies
def compare_counter(value: int, db: MyDatabase = arc.inject()) -> None:
    if value > db.value:
        print("Value is bigger!")
    else:
        print("Counter is bigger or equal!")


# Note that using 'arc.inject()' outside a command, or a function decorated with 'arc.inject_dependencies'
# will lead to unexpected behavior.

# Commands are automatically injected with dependencies, thus using '@arc.inject_dependencies' on them is redundant.

bot.run()
