# Daeqhipao

A computer interface to play the Game of Gods.

The game was created by Barbara Terlouw, and all intellectual property in it is hers.

# Installation

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and dependencies. [Install uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```
git clone https://github.com/CatarinaCarolina/Daeqhipao.git
cd Daeqhipao
uv sync
```

`uv sync` downloads the right Python version, creates a virtual environment in `.venv/` and installs the dependencies (pygame) from `uv.lock`.

# Run app

```
uv run daeqhipao
```

![image](https://user-images.githubusercontent.com/37830964/125526088-c85aefde-3979-49cb-bd21-418a9c35472c.png)

# Development

- Add a dependency: `uv add <package>` (updates `pyproject.toml` and `uv.lock`)
- Run any command inside the environment: `uv run <command>`, e.g. `uv run python`

# Contributions

Once all pieces and functionalies relating to the board and game objects have been implemented, contributions are very welcome! So is playtesting.

# AI assistance

All development on this fork was made with the help of Claude Code, Anthropic's AI coding assistant.

# Copyright

Copyright © 2021 Barbara Terlouw. All rights reserved.
