from __future__ import annotations

import sys
import typing as t

if t.TYPE_CHECKING:
    from .internal.types import ClientT


def loader(callback: t.Callable[[ClientT], None]) -> t.Callable[[ClientT], None]:
    """First-order decorator to set the load callback for this module.

    Usage
    -----
    ```py
    client.load_extension("my_extension")

    # In my_extension.py:

    @arc.loader
    def load(client: arc.Client) -> None:
        client.add_plugin(...)
    ```

    See Also
    --------
    - [`Client.load_extension`][arc.client.Client.load_extension]
    """
    module = sys.modules[callback.__module__]
    setattr(module, "__arc_extension_loader__", callback)
    return callback


def unloader(callback: t.Callable[[ClientT], None]) -> t.Callable[[ClientT], None]:
    """First-order decorator to set the unload callback for this module.

    Usage
    -----
    ```py
    client.unload_extension("my_extension")

    # In my_extension.py:

    @arc.unloader
    def unload(client: arc.Client) -> None:
        client.remove_plugin(...)
    ```

    See Also
    --------
    - [`Client.unload_extension`][arc.client.Client.unload_extension]
    """
    module = sys.modules[callback.__module__]
    setattr(module, "__arc_extension_unloader__", callback)
    return callback
