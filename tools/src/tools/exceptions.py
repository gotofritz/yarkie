# tools/exceptions.py

"""Provide exceptions used across the repository."""


class PlaylistExistException(Exception):
    """
    Exception raised when attempting to create a playlist that already exists.

    This exception is raised if there is an attempt to create a playlist in the
    database when a playlist with the same key already exists.
    """
