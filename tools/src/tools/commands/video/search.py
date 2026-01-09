# tools/commands/video/search.py

"""Search for videos with filters."""

import click

from tools.app_context import AppContext


@click.command()
@click.option(
    "--downloaded",
    type=click.Choice(["0", "1"], case_sensitive=False),
    help="Filter by downloaded status (0=not downloaded, 1=downloaded).",
)
@click.option(
    "--deleted",
    type=click.Choice(["0", "1"], case_sensitive=False),
    help="Filter by deleted status (0=not deleted, 1=deleted).",
)
@click.option(
    "--limit",
    type=int,
    help="Maximum number of videos to return.",
)
@click.pass_context
def search(
    ctx: click.Context,
    *,
    downloaded: str | None = None,
    deleted: str | None = None,
    limit: int | None = None,
) -> None:
    """Search for videos with optional filters.

    Examples:

        # Find all videos not yet downloaded
        tools video search --downloaded 0

        # Find deleted videos
        tools video search --deleted 1

        # Find first 10 non-downloaded videos
        tools video search --downloaded 0 --limit 10

    Args:
        ctx: Click context object.
        downloaded: Filter by downloaded status (0 or 1).
        deleted: Filter by deleted status (0 or 1).
        limit: Maximum number of videos to return.
    """
    app_context: AppContext = ctx.obj

    # Convert string options to boolean
    downloaded_bool = None if downloaded is None else (downloaded == "1")
    deleted_bool = None if deleted is None else (deleted == "1")

    videos = app_context.video_repository.get_videos(
        downloaded=downloaded_bool,
        deleted=deleted_bool,
        limit=limit,
    )

    if not videos:
        click.echo("No videos found matching the criteria.")
        return

    click.echo(f"Found {len(videos)} video(s):\n")
    for video in videos:
        status_flags = []
        if video.downloaded:
            status_flags.append("downloaded")
        if video.deleted:
            status_flags.append("deleted")
        status = f" [{', '.join(status_flags)}]" if status_flags else ""

        click.echo(f"  {video.id}: {video.title}{status}")