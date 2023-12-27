import hikari
import pytest

import arc

bot = hikari.GatewayBot("...", banner=None)
client = arc.GatewayClient(bot)


class Dummy:
    def __init__(self, val: int):
        self.val = val


client.set_type_dependency(Dummy, Dummy(0))


@client.inject_dependencies
def dummy_callback(dummy: Dummy = arc.inject()) -> int:
    dummy.val += 1
    return dummy.val


@client.inject_dependencies
async def async_dummy_callback(dummy: Dummy = arc.inject()) -> int:
    dummy.val += 1
    return dummy.val


@pytest.mark.asyncio
async def test_inject() -> None:
    assert dummy_callback() == 1
    assert await async_dummy_callback() == 2
    assert dummy_callback() == 3
