# tools/commands/discogs/postprocess.py

"""Command to update database with Discogs information interactively."""

import json

import click
from discogs_client.exceptions import HTTPError

from tools.app_context import AppContext
from tools.commands.helpers import prompt_numbered_choice
from tools.services.discogs_search_service import DiscogsSearchService
from tools.services.discogs_service import create_discogs_service


@click.command()
@click.pass_context
def postprocess(ctx: click.Context) -> None:
    """
    Interactive command to update DB with Discogs information.

    This command iterates through videos without Discogs metadata,
    searches for matching releases, and prompts the user to select
    the correct release, artists, and tracks.
    """
    app_context: AppContext = ctx.obj
    logger = app_context.logger
    logger.debug("Starting postprocess command")

    # Create services
    search_service = DiscogsSearchService(logger=logger)
    discogs_service = create_discogs_service(
        discogs_repository=app_context.discogs_repository,
        search_service=search_service,
        config=app_context.config,
        logger=logger,
    )

    offset = 0
    while to_search := discogs_service.get_next_video_to_process(offset=offset):
        (video_id, search_strings) = to_search
        offset += 1

        # Prompt user to select or enter search string
        click.echo("\n---------------------------------\nPossible search strings:")
        search_string = prompt_numbered_choice(
            search_strings,
            prompt_text="Select search string or enter your own",
            allow_custom=True,
        )

        if not search_string:
            click.echo(f"Skipping {video_id}")
            continue

        # Search for releases
        results = discogs_service.search_releases(search_string=search_string)

        # Handle no results - prompt for ID
        if len(results) == 0:
            search_string = click.prompt(
                "No results found. Do you have an ID?",
                type=str,
                default="",
                show_default=False,
            )
            if search_string:
                try:
                    results = [discogs_service.get_release_by_id(release_id=int(search_string))]
                    logger.info(f"Found {len(results)} results")
                except HTTPError as e:
                    if e.status_code == 404:
                        click.echo("No results found")
                        continue
                    else:
                        raise e
            else:
                continue

        # Handle multiple results - let user select
        master = None
        if len(results) > 1:
            click.echo(f"Found {len(results)} results")

            # Filter and prioritize results
            prioritised = discogs_service.filter_and_prioritize_releases(results=results)

            selected = prompt_numbered_choice(
                prioritised,
                formatter=lambda idx, result: f"{idx}. {result.title}",
                prompt_text="Which release?",
                allow_custom=True,
                allow_quit=True,
            )

            if selected is None:
                # User quit
                break

            if isinstance(selected, str):
                # User entered custom search - retry
                results = discogs_service.search_releases(search_string=selected)
                if len(results) == 0:
                    click.echo("No results found")
                    continue

                if len(results) > 1:
                    click.echo(f"Found {len(results)} results")
                    nested_selected = prompt_numbered_choice(
                        results,
                        formatter=lambda idx, result: f"{idx}. {result.title}",
                        prompt_text="Which release?",
                        allow_quit=True,
                        allow_custom=False,
                    )

                    if nested_selected is None:
                        # User quit or invalid selection
                        break

                    master = nested_selected
                else:
                    master = results[0]
            else:
                master = selected
        else:
            master = results[0]

        if master is None:
            click.echo("No release selected, skipping")
            continue

        # Type narrowing: master should be a Release object, not a string
        # The isinstance(selected, str) branch above handles custom searches
        assert not isinstance(master, str), "master should be a Release object"

        # Save release to database
        # Handle both Master objects (from search) and Release objects (from ID lookup)
        # Masters have data in .data dict, Releases have direct attributes
        if hasattr(master, "data") and isinstance(master.data, dict):
            # Master object from search results
            _ = master.data["title"]  # Force lazy loading
            release_data = {
                "id": master.id,
                "title": master.data["title"],
                "country": master.data["country"],
                "genres": master.genres,
                "styles": master.styles,
                "year": master.year,
                "url": master.url,
            }
            potential_artists = [artist for artist in master.data["artists"]]
        else:
            # Release object from get_release_by_id
            release_data = {
                "id": master.id,
                "title": master.title,
                "country": master.country,
                "genres": master.genres,
                "styles": master.styles,
                "year": master.year,
                "url": master.url,
            }
            potential_artists = [artist for artist in master.artists]

        release_id = discogs_service.save_release(release_data=release_data)
        logger.debug(f"Created release {release_id}")

        # Process artists
        artists_to_add = []

        # Prompt user to select artists from release
        for artist in potential_artists:
            click.echo(json.dumps(artist, indent=2))
            yes_or_no = click.confirm("Use artist?", default=True, show_default=True)
            if not yes_or_no:
                continue

            try:
                artist_obj = discogs_service.get_artist_by_id(artist_id=artist["id"])
                artists_to_add.append(
                    {
                        "id": artist_obj.id,
                        "name": discogs_service.clean_artist_name(name=artist_obj.name),
                        "profile": artist_obj.profile,
                        "uri": artist_obj.url,
                        "role": artist_obj.role,
                    }
                )
            except HTTPError as e:
                if e.status_code == 404:
                    click.echo(f"Weird Discogs error: {artist['id']} not found")
                    continue

        # If no artists selected, allow manual search
        if not artists_to_add:
            artist_search = click.prompt(
                "Could not find artist, do you want to search manually?",
                type=str,
                default="",
            )
            if not artist_search:
                click.echo("Not searching")
                continue

            potential_artists_search = discogs_service.search_artists(search_string=artist_search)
            for artist_obj in potential_artists_search:
                click.echo(json.dumps(artist_obj.data, indent=2))
                choice = click.prompt(
                    "Use artist?",
                    default="y",
                    show_choices=True,
                    type=click.Choice(["y", "n", "q"]),
                    show_default=True,
                )
                if choice == "q":
                    break
                if choice == "n" or choice == "N":
                    continue

                try:
                    artists_to_add.append(
                        {
                            "id": artist_obj.id,
                            "name": artist_obj.name,
                            "profile": artist_obj.profile,
                            "uri": artist_obj.url,
                            "role": artist_obj.role,
                        }
                    )
                except HTTPError as e:
                    if e.status_code == 404:
                        click.echo("Weird Discogs error: artist not found")
                        continue

        if not artists_to_add:
            click.echo("No artists found, skipping to next release")
            continue

        # Save all selected artists
        for artist_obj in artists_to_add:
            discogs_service.save_artist(
                artist_data=artist_obj,
                release_id=release_id,
                role=artist_obj["role"],
            )
            logger.debug(f"Created artist {artist_obj['name']}")

        # Process tracks
        click.echo(f"This release has {len(master.tracklist)} tracks")

        selected_track = prompt_numbered_choice(
            list(master.tracklist),
            formatter=lambda idx, track: f"{idx}. {track.title}",
            prompt_text="Which track?",
            allow_quit=True,
        )

        if selected_track is None:
            # User quit or invalid selection
            break

        # Type narrowing: selected_track should be a Track object
        assert not isinstance(selected_track, str), "selected_track should be a Track object"

        track = selected_track.data
        discogs_service.save_track(
            track_data={
                "release_id": master.id,
                "title": track["title"],
                "duration": track["duration"],
                "position": track["position"],
                "type_": track["type_"],
            },
            video_id=video_id,
        )

    click.echo("Finished")
