import os
import re
import types
import typing as t

from setuptools import find_namespace_packages, setup

name = "arc"


def parse_meta() -> types.SimpleNamespace:
    with open(os.path.join(name, "internal", "about.py")) as fp:
        code = fp.read()

    token_pattern = re.compile(
        r"^__(?P<key>\w+)?__\s*:?.*=\s*(?P<quote>(?:'{3}|\"{3}|'|\"))(?P<value>.*?)(?P=quote)", re.M
    )

    groups = {}

    for match in token_pattern.finditer(code):
        group = match.groupdict()
        groups[group["key"]] = group["value"]

    return types.SimpleNamespace(**groups)


def long_description() -> str:
    with open("README.md") as fp:
        return fp.read()


def parse_requirements_file(path: str) -> t.List[str]:
    with open(path) as fp:
        dependencies = (d.strip() for d in fp.read().split("\n") if d.strip())
        return [d for d in dependencies if not d.startswith("#")]


meta = parse_meta()

setup(
    name="hikari-arc",
    version=meta.version,
    description="A command handler for hikari with a focus on type-safety and correctness.",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    author=meta.author,
    author_email=meta.author_email,
    maintainer=meta.maintainer,
    url=meta.url,
    packages=find_namespace_packages(include=[name + "*"]),
    package_data={"arc": ["py.typed"]},
    license=meta.license,
    include_package_data=True,
    zip_safe=False,
    install_requires=parse_requirements_file("requirements.txt"),
    extras_require={
        ':sys_platform=="win32"': ["colorama"],
        "docs": parse_requirements_file("doc_requirements.txt"),
        "dev": parse_requirements_file("dev_requirements.txt"),
        "rest": parse_requirements_file("rest_requirements.txt"),
        "cron": parse_requirements_file("cron_requirements.txt"),
    },
    python_requires=">=3.10.0,<3.14",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
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
