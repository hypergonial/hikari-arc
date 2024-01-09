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

    Examples
    --------
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

    Examples
    --------
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


# MIT License
#
# Copyright (c) 2023-present hypergonial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
