import typing as t

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


@client.inject_dependencies
def injects_client(client: arc.abc.Client[t.Any] = arc.inject()) -> arc.abc.Client[t.Any]:
    return client


@client.inject_dependencies  # type: ignore
def injects_client_improperly_typed(client: arc.abc.Client = arc.inject()) -> arc.abc.Client:  # type: ignore
    return client  # type: ignore


@client.inject_dependencies
def injects_exact_client(client: arc.GatewayClient = arc.inject()) -> arc.GatewayClient:
    return client


injector = arc.Injector()
injector.set_type_dependency(Dummy, Dummy(0))

manually_injected_client = arc.GatewayClient(bot, injector=injector)


@manually_injected_client.inject_dependencies
def manual_dummy_callback(dummy: Dummy = arc.inject()) -> int:
    dummy.val += 1
    return dummy.val


@pytest.mark.asyncio
async def test_inject() -> None:
    assert dummy_callback() == 1
    assert await async_dummy_callback() == 2
    assert dummy_callback() == 3
    assert injects_client() is client
    assert injects_client_improperly_typed() is client
    assert injects_exact_client() is client

    assert manual_dummy_callback() == 1
