import hikari

import arc

bot = hikari.RESTBot("...")
client = arc.RESTClient(bot)

# Related documentation guide: https://arc.hypergonial.com/guides/loops


# Create a loop out of a function
# This will call the function every 10 seconds when started
@arc.utils.interval_loop(seconds=10.0)
async def loopy_loop(value: int) -> None:
    print(value)


async def another_loop() -> None:
    print("Every 60 seconds, a minute passes")


# You may also create a loop using the class directly
loop = arc.utils.IntervalLoop(another_loop, seconds=60.0)


@client.add_startup_hook
async def startup(client: arc.RESTClient) -> None:
    # Start the loop by passing all the parameters it needs
    loopy_loop.start(value=10)

    # The other loop has no parameters, so you can just start it
    loop.start()


bot.run()
