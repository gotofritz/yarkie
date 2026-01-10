# tools/commands/discogs/postprocess.py

"""Command to update database with Discogs information interactively."""

import click
from tools.app_context import AppContext
from tools.services.discogs_interaction_strategy import CliInteractionStrategy
from tools.services.discogs_processor import DiscogsProcessor
from tools.services.discogs_search_service import DiscogsSearchService
from tools.services.discogs_service import create_discogs_service


@click.command()
@click.option(
    "--deterministic/--random",
    default=True,
    help="Process videos sequentially (deterministic) or randomly (random). Default is deterministic.",
)
@click.pass_context
def postprocess(ctx: click.Context, deterministic: bool) -> None:
    """
    Interactive command to update DB with Discogs information.

    This command iterates through videos without Discogs metadata,
    searches for matching releases, and prompts the user to select
    the correct release, artists, and tracks.

    Use --random to get a random video each time instead of sequential processing.
    This is useful when testing to avoid repeatedly encountering videos that
    cannot be found in Discogs.
    """
    app_context: AppContext = ctx.obj
    logger = app_context.logger
    logger.debug(
        f"Starting postprocess command (mode: {'deterministic' if deterministic else 'random'})"
    )

    # Create services
    search_service = DiscogsSearchService(logger=logger)
    discogs_service = create_discogs_service(
        discogs_repository=app_context.discogs_repository,
        search_service=search_service,
        config=app_context.config,
        logger=logger,
    )

    # Create processor with CLI interaction strategy
    interaction_strategy = CliInteractionStrategy()
    processor = DiscogsProcessor(
        discogs_service=discogs_service,
        interaction_strategy=interaction_strategy,
        logger=logger,
    )

    # Process videos in loop
    offset = 0
    while to_search := discogs_service.get_next_video_to_process(
        offset=offset, deterministic=deterministic
    ):
        (video_id, search_strings) = to_search

        # Only increment offset in deterministic mode
        if deterministic:
            offset += 1

        # Process the video using DiscogsProcessor
        result = processor.process_video(
            video_id=video_id,
            search_strings=search_strings,
        )

        # Handle result
        if result.success:
            click.echo(f"\n✓ Successfully processed {video_id}")
            click.echo(f"  Release: {result.release_id}")
            click.echo(f"  Artists: {len(result.artist_ids)}")
            click.echo(f"  Track: {result.track_id}")
        else:
            click.echo(f"\n⊘ {result.message}")
            # If there was an error, check if user wants to continue
            if result.error and not interaction_strategy.should_continue_after_error(
                error=result.error
            ):
                click.echo("User quit processing")
                break

    click.echo("\nFinished")
