__all__ = ("ArcError", "AutocompleteError", "CommandInvokeError")


class ArcError(Exception):
    """Base exception for all Arc errors."""


class AutocompleteError(ArcError):
    """An erro occurred while trying to autocomplete a command."""


class CommandInvokeError(ArcError):
    """An error occurred while trying to invoke a command."""


class ExtensionError(ArcError):
    """A base exception for all extension errors."""


class ExtensionLoadError(ExtensionError):
    """An error occurred while trying to load an extension."""


class ExtensionUnloadError(ExtensionError):
    """An error occurred while trying to unload an extension."""


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
