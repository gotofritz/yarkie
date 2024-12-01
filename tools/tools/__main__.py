"""Serve as the entry point when running the as a script."""

from tools.cli import cli

if __name__ == "__main__":
    # Invokes the Click command-line interface defined in cli.py when
    # executed as a script.
    cli()
