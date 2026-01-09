# tests/tools/commands/test_helpers.py

"""Tests for command helper functions."""

from unittest.mock import patch

from tools.commands.helpers import prompt_numbered_choice


def test_empty_list_returns_none():
    """Test that empty list returns None without prompting."""
    result = prompt_numbered_choice([])
    assert result is None


def test_valid_numeric_selection():
    """Test selecting an item by its number."""
    items = ["apple", "banana", "cherry"]

    with patch("tools.commands.helpers.click.prompt", return_value="2"):
        result = prompt_numbered_choice(items)

    assert result == "banana"


def test_numeric_selection_first_item():
    """Test selecting the first item."""
    items = ["first", "second", "third"]

    with patch("tools.commands.helpers.click.prompt", return_value="1"):
        result = prompt_numbered_choice(items)

    assert result == "first"


def test_numeric_selection_last_item():
    """Test selecting the last item."""
    items = ["first", "second", "third"]

    with patch("tools.commands.helpers.click.prompt", return_value="3"):
        result = prompt_numbered_choice(items)

    assert result == "third"


def test_out_of_range_selection_returns_none():
    """Test that out of range number returns None."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="5"):
        result = prompt_numbered_choice(items)

    assert result is None


def test_zero_selection_returns_none():
    """Test that zero returns None."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="0"):
        result = prompt_numbered_choice(items)

    assert result is None


def test_negative_selection_returns_none():
    """Test that negative number returns None."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="-1"):
        result = prompt_numbered_choice(items)

    assert result is None


def test_non_numeric_input_without_allow_custom_returns_none():
    """Test that non-numeric input returns None when allow_custom=False."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="invalid"):
        result = prompt_numbered_choice(items, allow_custom=False)

    assert result is None


def test_custom_input_with_allow_custom():
    """Test that custom text is returned when allow_custom=True."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="custom search"):
        result = prompt_numbered_choice(items, allow_custom=True)

    assert result == "custom search"


def test_empty_string_returns_none():
    """Test that empty string returns None."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value=""):
        result = prompt_numbered_choice(items)

    assert result is None


def test_quit_with_allow_quit_true():
    """Test that 'q' returns None when allow_quit=True."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="q"):
        result = prompt_numbered_choice(items, allow_quit=True)

    assert result is None


def test_quit_uppercase_with_allow_quit_true():
    """Test that 'Q' returns None when allow_quit=True."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="Q"):
        result = prompt_numbered_choice(items, allow_quit=True)

    assert result is None


def test_quit_without_allow_quit_returns_none():
    """Test that 'q' is treated as invalid when allow_quit=False."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt", return_value="q"):
        result = prompt_numbered_choice(items, allow_quit=False)

    assert result is None


def test_custom_formatter():
    """Test using a custom formatter function."""
    items = [{"name": "apple", "color": "red"}, {"name": "banana", "color": "yellow"}]

    def custom_formatter(idx: int, item: dict) -> str:
        return f"{idx}. {item['name']} ({item['color']})"

    with patch("tools.commands.helpers.click.echo") as mock_echo:
        with patch("tools.commands.helpers.click.prompt", return_value="1"):
            result = prompt_numbered_choice(items, formatter=custom_formatter)

    # Verify formatter was used
    mock_echo.assert_any_call("1. apple (red)")
    mock_echo.assert_any_call("2. banana (yellow)")
    assert result == {"name": "apple", "color": "red"}


def test_custom_prompt_text():
    """Test using custom prompt text."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt") as mock_prompt:
        mock_prompt.return_value = "1"
        prompt_numbered_choice(items, prompt_text="Choose a fruit")

    # Verify custom prompt text was used
    mock_prompt.assert_called_once()
    call_args = mock_prompt.call_args
    assert "Choose a fruit (1-2)" == call_args[0][0]


def test_prompt_includes_quit_option_when_enabled():
    """Test that prompt text includes quit instruction when allow_quit=True."""
    items = ["apple", "banana"]

    with patch("tools.commands.helpers.click.prompt") as mock_prompt:
        mock_prompt.return_value = "1"
        prompt_numbered_choice(items, allow_quit=True)

    # Verify prompt includes quit instruction
    call_args = mock_prompt.call_args
    prompt_text = call_args[0][0]
    assert "q" in prompt_text.lower()
    assert "quit" in prompt_text.lower()


def test_default_formatter_with_string_items():
    """Test default formatter displays items correctly."""
    items = ["apple", "banana", "cherry"]

    with patch("tools.commands.helpers.click.echo") as mock_echo:
        with patch("tools.commands.helpers.click.prompt", return_value="1"):
            prompt_numbered_choice(items)

    # Verify default format was used
    mock_echo.assert_any_call("1. apple")
    mock_echo.assert_any_call("2. banana")
    mock_echo.assert_any_call("3. cherry")


def test_works_with_complex_objects():
    """Test that function works with complex objects."""

    class Release:
        def __init__(self, title: str):
            self.title = title

        def __str__(self):
            return self.title

    items = [Release("Album 1"), Release("Album 2")]

    with patch("tools.commands.helpers.click.prompt", return_value="2"):
        result = prompt_numbered_choice(items)

    assert result.title == "Album 2"


def test_combined_flags_custom_and_quit():
    """Test that allow_custom and allow_quit work together."""
    items = ["apple", "banana"]

    # Test quit takes precedence
    with patch("tools.commands.helpers.click.prompt", return_value="q"):
        result = prompt_numbered_choice(items, allow_custom=True, allow_quit=True)
    assert result is None

    # Test custom input works
    with patch("tools.commands.helpers.click.prompt", return_value="custom"):
        result = prompt_numbered_choice(items, allow_custom=True, allow_quit=True)
    assert result == "custom"

    # Test numeric selection still works
    with patch("tools.commands.helpers.click.prompt", return_value="1"):
        result = prompt_numbered_choice(items, allow_custom=True, allow_quit=True)
    assert result == "apple"