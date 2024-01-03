from __future__ import annotations

import sys
import typing as t

if t.TYPE_CHECKING:
    from arc.internal.types import ClientT


@t.overload
def loader() -> t.Callable[[t.Callable[[ClientT], None]], t.Callable[[ClientT], None]]:
    ...


@t.overload
def loader(callback: t.Callable[[ClientT], None]) -> t.Callable[[ClientT], None]:
    ...


def loader(
    callback: t.Callable[[ClientT], None] | None = None,
) -> t.Callable[[ClientT], None] | t.Callable[[t.Callable[[ClientT], None]], t.Callable[[ClientT], None]]:
    """Decorator to set the load callback for this module.

    Usage
    -----
    ```py
    client.load_extension("my_extension")

    # In my_extension.py:

    @arc.loader
    def load(client: arc.GatewayClient) -> None:
        client.add_plugin(...)
    ```

    See Also
    --------
    - [`Client.load_extension`][arc.client.Client.load_extension]
    """

    def decorator(func: t.Callable[[ClientT], None]) -> t.Callable[[ClientT], None]:
        module = sys.modules[func.__module__]
        setattr(module, "__arc_extension_loader__", func)
        return func

    if callback is not None:
        return decorator(callback)

    return decorator


@t.overload
def unloader() -> t.Callable[[t.Callable[[ClientT], None]], t.Callable[[ClientT], None]]:
    ...


@t.overload
def unloader(callback: t.Callable[[ClientT], None]) -> t.Callable[[ClientT], None]:
    ...


def unloader(
    callback: t.Callable[[ClientT], None] | None = None,
) -> t.Callable[[ClientT], None] | t.Callable[[t.Callable[[ClientT], None]], t.Callable[[ClientT], None]]:
    """Decorator to set the unload callback for this module.

    Usage
    -----
    ```py
    client.unload_extension("my_extension")

    # In my_extension.py:

    @arc.unloader
    def unload(client: arc.GatewayClient) -> None:
        client.remove_plugin(...)
    ```

    See Also
    --------
    - [`Client.unload_extension`][arc.client.Client.unload_extension]
    """

    def decorator(func: t.Callable[[ClientT], None]) -> t.Callable[[ClientT], None]:
        module = sys.modules[func.__module__]
        setattr(module, "__arc_extension_unloader__", func)
        return func

    if callback is not None:
        return decorator(callback)

    return decorator
