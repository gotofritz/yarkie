"""
Common helper functions for CLI commands.

This module provides utilities for reducing boilerplate in interactive commands.
"""

from collections.abc import Callable
from typing import TypeVar

import click

T = TypeVar("T")


def prompt_numbered_choice(
    items: list[T],
    *,
    formatter: Callable[[int, T], str] | None = None,
    prompt_text: str = "Select option",
    allow_custom: bool = False,
    allow_quit: bool = False,
) -> T | str | None:
    """
    Display a numbered list and prompt user to select an item.

    Args:
        items: List of items to choose from
        formatter: Optional function to format each item for display.
                  Takes (index, item) and returns display string.
                  Default: "{index}. {item}"
        prompt_text: Text to show in the selection prompt
        allow_custom: If True, user can enter custom text instead of number
        allow_quit: If True, user can enter 'q' to quit

    Returns:
        Selected item from list, or custom string if allow_custom=True,
        or None if user quit

    Example:
        >>> items = ["apple", "banana", "cherry"]
        >>> choice = prompt_numbered_choice(items, prompt_text="Pick a fruit")
        1. apple
        2. banana
        3. cherry
        Pick a fruit (1-3): 2
        >>> choice
        'banana'
    """
    if not items:
        return None

    # Display numbered options
    for idx, item in enumerate(items, 1):
        if formatter:
            display = formatter(idx, item)
        else:
            display = f"{idx}. {item}"
        click.echo(display)

    # Build prompt text with range
    full_prompt = f"{prompt_text} (1-{len(items)})"
    if allow_quit:
        full_prompt += " or 'q' to quit"

    # Get user selection
    selection = click.prompt(
        full_prompt,
        type=str,
        default="",
        show_default=False,
    )

    # Handle quit
    if allow_quit and selection.lower() == "q":
        return None

    # Handle numeric selection
    if selection.isdigit():
        idx = int(selection)
        if 1 <= idx <= len(items):
            return items[idx - 1]

    # Handle custom input
    if allow_custom and selection:
        return selection

    # Invalid selection
    return None
