# Yarkie Tools

Yarkie Tools is a collection of helper scripts and setup utilities designed to streamline tasks related to the Yarkie project.

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

- Run specific linting tasks (e.g., isort, black, flake8):

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
