"""CLI entry point for arc."""
import os
import platform
import sys

import hikari

import arc

# Support color on Windows
if sys.platform == "win32":
    import colorama

    colorama.init()


TEAL = "\x1b[38;5;79m"
WHITE = "\x1b[37m"

uname = platform.uname()
system_details = f"{uname.system} {uname.machine} ({uname.node}) - {uname.release}"
python_details = f"{platform.python_implementation()} {platform.python_version()} ({platform.python_compiler()})"

sys.stderr.write(
    f"""{TEAL}hikari-arc - package information
{WHITE}--------------------------------
{TEAL}Arc version: {WHITE}{arc.__version__}
{TEAL}Install path: {WHITE}{os.path.abspath(os.path.dirname(__file__))}
{TEAL}Hikari version: {WHITE}{hikari.__version__}
{TEAL}Install path: {WHITE}{os.path.abspath(os.path.dirname(hikari.__file__))}
{TEAL}Python: {WHITE}{python_details}
{TEAL}System: {WHITE}{system_details}\n\n"""
)

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
