# Contributing

All contributions are welcome, no matter how small! However there are some caveats to be aware of, detailed below.

## Open an issue

If your contribution is **not** a bugfix or small change, please [open an issue](https://github.com/hypergonial/hikari-arc/issues/new/choose) or contact me on [Discord](https://discord.gg/hikari) to discuss it.

## Setting up the project

### Installing dependencies

`arc` uses [`uv`](https://github.com/astral-sh/uv) for dependency management, you should [install it](https://docs.astral.sh/uv/getting-started/installation/#installing-uv) if you haven't already.

Use the command below to install all the tooling required to develop arc in a virtual environment:

```sh
$ uv sync --all-extras --dev
```

### Running nox

Before submitting your changes, you should run [`nox`](https://pypi.org/project/nox/) and ensure all the pipelines pass successfully.
This checks the code for typing errors, antipatterns & bad practices, along with formatting it & running all tests.

```sh
uv run nox
```

GitHub CI runs on every pull request to verify that `nox` passes.

### Configuring your editor

This is optional, but highly recommended if you're doing larger contributions.

#### VS Code

When cloning the project for the first time, VS Code should prompt you to install extensions recommended by the project, if you're missing any. Review and install them.

This should set up linting & typechecking to be performed as you edit the source code, along with defaulting the formatter to [`ruff`](https://astral.sh/ruff). A fairly minimal [editorconfig](https://editorconfig.org) is also applied to ensure consistency with the rest of the project.

You can also run `nox` by using the shortcut Ctrl+Shift+B. This uses VS Code's tasks system, [see here](https://go.microsoft.com/fwlink/?LinkId=733558) for more information.

Custom snippets are also available:

- `!!!` + TAB: Set up a new source file, insert annotations import & license

#### PyCharm and other JetBrains IDEs

Configuration should be applied automatically, however there is no good extension for [`ruff`](https://astral.sh/ruff), so you should doubly make sure `nox` successfully completes before committing your changes.

#### Other editors

If you want to add explicit support for other editors, please [open a PR](https://github.com/hypergonial/hikari-arc/pulls)!

---

That's all! Thanks for reading it all. If you have suggestions as to what other things should be added here to improve the developer experience, please [open an issue](https://github.com/hypergonial/hikari-arc/issues/new/choose)!
