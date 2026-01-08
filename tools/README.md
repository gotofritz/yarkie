# Yarkie Tools

![QA Status](https://github.com/gotofritz/yarkie/actions/workflows/qa.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-20%25-orange)

Yarkie Tools is a collection of helper scripts and setup utilities designed to streamline tasks related to the Yarkie project.

## Current Status

The project is undergoing architectural cleanup to improve modularity and maintainability. See [docs/project-plan.md](docs/project-plan.md) for the detailed refactoring plan.

**Recent improvements:**
- ✅ Modernized project structure with `src/` layout
- ✅ Replaced mypy with ty for type checking
- ✅ Added GitHub Actions workflow for automated QA checks
- ✅ Unified configuration using Pydantic-based settings

## Table of Contents

- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Tasks](#tasks)
- [Contributing](#contributing)
- [License](#license)

## Description

The Yarkie Tools project provides a set of command-line utilities and scripts to assist in various aspects of the Yarkie project. It includes functionalities for managing data, handling playlists, and incorporating testing and linting tools.

## Installation

To set up Yarkie Tools, follow these steps:

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/gotofritz/yarkie.git
   ```

2. Navigate to the project directory:

   ```bash
   cd yarkie
   ```

3. Create a virtual environment and activate it:

   ```bash
   uv sync
   source .venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

## Usage

Yarkie Tools provides a command-line interface (CLI) for executing various tasks. Here are some common commands:

- Run linting and tests:

  ```bash
  task qa
  ```

- Run specific linting tasks (ruff and ty):

  ```bash
  task lint
  ```

- Run tests:

  ```bash
  task test
  ```

For more details on available tasks, refer to the [Taskfile](Taskfile.yml).

## Tasks

The project includes a set of tasks defined in the [Taskfile](Taskfile.yml). These tasks cover linting, testing, code formatting, and more. You can customize and extend these tasks based on your project's needs.

## Contributing

Contributions are welcome! If you find issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
