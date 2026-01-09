# tools/commands/video/delete.py

"""Delete videos from the database and optionally from disk."""

import click

from tools.app_context import AppContext


@click.command()
@click.argument("video_ids", nargs=-1, required=True)
@click.option(
    "--no-files",
    is_flag=True,
    help="Do not delete video and thumbnail files from disk.",
)
@click.pass_context
def delete(
    ctx: click.Context,
    *,
    video_ids: tuple[str, ...],
    no_files: bool = False,
) -> None:
    """Delete one or more videos from the database.

    By default, this command also deletes the video and thumbnail files
    from disk. Use --no-files to keep the files.

    Examples:

        # Delete a single video
        tools video delete yv3dtaM_x3U

        # Delete multiple videos
        tools video delete yv3dtaM_x3U bJ9r8LMU9bQ

        # Delete video from database but keep files
        tools video delete yv3dtaM_x3U --no-files

    Args:
        ctx: Click context object.
        video_ids: One or more video IDs to delete.
        no_files: If True, keep video/thumbnail files on disk.
    """
    app_context: AppContext = ctx.obj

    delete_files = not no_files

    click.echo(f"Deleting {len(video_ids)} video(s)...")

    deleted_count = app_context.video_repository.delete_videos(
        video_ids=list(video_ids),
        delete_files=delete_files,
    )

    if deleted_count > 0:
        click.echo(f"Successfully deleted {deleted_count} video(s).")
        if delete_files:
            click.echo("Video and thumbnail files were also removed from disk.")
    else:
        click.echo("No videos were deleted. Check the video IDs and try again.")