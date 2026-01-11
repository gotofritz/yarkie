# tools/commands/discogs/update.py

"""Command to update Discogs metadata for a specific video."""

import click

from tools.app_context import AppContext
from tools.services.discogs_interaction_strategy import CliInteractionStrategy
from tools.services.discogs_processor import DiscogsProcessor
from tools.services.discogs_search_service import DiscogsSearchService
from tools.services.discogs_service import create_discogs_service


@click.command()
@click.argument("video_id")
@click.pass_context
def update(ctx: click.Context, video_id: str) -> None:
    """
    Update Discogs metadata for a specific video.

    Applies the same multistep processing as 'postprocess' but targets
    a single video by ID.

    Example:
        tools discogs update abc123xyz
    """
    app_context: AppContext = ctx.obj
    logger = app_context.logger
    logger.debug(f"Starting update command for video {video_id}")

    # Get video and generate search strings
    video = app_context.video_repository.get_video_by_id(video_id=video_id)
    if not video:
        click.echo(f"Error: Video '{video_id}' not found")
        ctx.exit(1)

    # Create services
    search_service = DiscogsSearchService(logger=logger)
    discogs_service = create_discogs_service(
        discogs_repository=app_context.discogs_repository,
        search_service=search_service,
        config=app_context.config,
        logger=logger,
    )

    # Generate search strings from video metadata
    search_strings = search_service.generate_search_strings(
        title=video.title,
        uploader=video.uploader,
        description=video.description,
    )

    # Create processor with CLI interaction
    interaction_strategy = CliInteractionStrategy()
    processor = DiscogsProcessor(
        discogs_service=discogs_service,
        interaction_strategy=interaction_strategy,
        logger=logger,
    )

    # Process single video
    result = processor.process_video(
        video_id=video_id,
        search_strings=search_strings,
    )

    if result.success:
        click.echo(f"\n✓ Successfully updated {video_id}")
        click.echo(f"  Release: {result.release_id}")
        click.echo(f"  Artists: {len(result.artist_ids)}")
        click.echo(f"  Track: {result.track_id}")
    else:
        click.echo(f"\n✗ Failed to update {video_id}: {result.message}")
        ctx.exit(1)
