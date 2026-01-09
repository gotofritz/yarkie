# tools/commands/playlist/disable.py

"""Disable playlists in the database."""

import click

from tools.app_context import AppContext


@click.command()
@click.argument("playlist_ids", nargs=-1, required=True)
@click.pass_context
def disable(
    ctx: click.Context,
    *,
    playlist_ids: tuple[str, ...],
) -> None:
    """Disable one or more playlists.

    Disabled playlists will not be included in future refresh operations.

    Examples:

        # Disable a single playlist
        tools playlist disable PLZ6Ih9wLHQ2ERz4K8fHzyvvdxG0pxlMQL

        # Disable multiple playlists
        tools playlist disable PLAYLIST_ID1 PLAYLIST_ID2

    Args:
        ctx: Click context object.
        playlist_ids: One or more playlist IDs to disable.
    """
    app_context: AppContext = ctx.obj

    click.echo(f"Disabling {len(playlist_ids)} playlist(s)...")

    disabled_count = app_context.playlist_repository.disable_playlists(
        playlist_ids=list(playlist_ids)
    )

    if disabled_count > 0:
        click.echo(f"Successfully disabled {disabled_count} playlist(s).")
    else:
        click.echo("No playlists were disabled. Check the playlist IDs and try again.")
