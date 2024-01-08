import hikari

import arc

bot = hikari.GatewayBot("...", banner=None)
client = arc.GatewayClient(bot)


def test_ext_load() -> None:
    client.load_extension("extension")
    assert len(client.plugins) == 1
    assert client.plugins["test_plugin"].name == "test_plugin"
    assert len(client._slash_commands) == 4
    assert {"foo", "bar", "baz", "my_group"} == set(client._slash_commands.keys())
