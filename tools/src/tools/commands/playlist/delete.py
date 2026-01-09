# tools/commands/playlist/delete.py

"""Delete playlists from the database."""

import click

from tools.app_context import AppContext


@click.command()
@click.argument("playlist_ids", nargs=-1, required=True)
@click.pass_context
def delete(
    ctx: click.Context,
    *,
    playlist_ids: tuple[str, ...],
) -> None:
    """Delete one or more playlists from the database.

    This command deletes both the playlist records and their associated
    video entries.

    Examples:

        # Delete a single playlist
        tools playlist delete PLZ6Ih9wLHQ2ERz4K8fHzyvvdxG0pxlMQL

        # Delete multiple playlists
        tools playlist delete PLAYLIST_ID1 PLAYLIST_ID2

    Args:
        ctx: Click context object.
        playlist_ids: One or more playlist IDs to delete.
    """
    app_context: AppContext = ctx.obj

    click.echo(f"Deleting {len(playlist_ids)} playlist(s)...")

    deleted_count = app_context.playlist_repository.delete_playlists(
        playlist_ids=list(playlist_ids)
    )

    if deleted_count > 0:
        click.echo(f"Successfully deleted {deleted_count} playlist(s) and their entries.")
    else:
        click.echo("No playlists were deleted. Check the playlist IDs and try again.")