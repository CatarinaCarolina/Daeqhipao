# Contributing to Daeqhipao

# Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then from the repository folder:

```
uv sync
uv run daeqhipao
```

`uv sync` also installs the development tools (Ruff and mypy).

# Before you commit

```
uv run ruff format      # format the code
uv run ruff check --fix # lint, fixing what can be fixed automatically
uv run mypy             # type check
```

All three should finish without errors.

# Coding standards

- **Formatting**: whatever `ruff format` produces (88-character lines, double quotes). Don't format by hand.
- **Naming**: [PEP 8](https://peps.python.org/pep-0008/#naming-conventions): `snake_case` for functions and variables, `CapWords` for classes, `UPPER_CASE` for constants.
- **Imports**: explicit names (`from daeqhipao.style import SQUARE_WIDTH`), no `import *`. Import a name from the module that defines it.
- **Type hints**: every function has annotated arguments and a return type; `mypy` runs in strict mode. Use modern syntax (`list[Field]`, `Field | None`). Imports needed only for type hints go under `if TYPE_CHECKING:`.
- **Docstrings**: [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for every module, class and public function. A one-line summary is enough when the name and type hints make the rest obvious; add `Args:`, `Returns:` and `Raises:` sections when they don't.
- **Comments**: explain *why*, not *what*.

The tool settings live in `pyproject.toml` under `[tool.ruff]` and `[tool.mypy]`.
