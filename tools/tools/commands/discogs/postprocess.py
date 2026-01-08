# tools/commands/playlist/refresh.py

"""Command to refresh new or existing playlists."""

import json
import re

import click
import discogs_client
from discogs_client.exceptions import HTTPError

from tools.app_context import AppContext
from tools.models.models import DiscogsArtist, DiscogsRelease, DiscogsTrack


@click.command()
@click.pass_context
def postprocess(ctx: click.Context) -> None:
    """
    Interactive command to Update DB with discogs information
    """
    app_context: AppContext = ctx.obj
    logger = app_context.logger
    logger.debug("Starting postprocess command")

    db = app_context.db
    d = discogs_client.Client("ExampleApplication/0.1", user_token=app_context.config.discogs_token)
    while to_search := db.next_without_discogs():
        (video_id, search_strings) = to_search
        click.echo("\n---------------------------------\nPossible search strings:")
        for idx, search_string in enumerate(search_strings, 1):
            click.echo(f"{idx}. {search_string}")

        search_string = click.prompt(
            f"Select search string (1-{len(search_strings)}) or enter your own",
            type=str,
            default="",
        )
        if search_string.isdigit():
            search_string = search_strings[int(search_string) - 1]

        if not search_string:
            click.echo(f"Skipping {video_id}")
            continue

        results = d.search(search_string, type="master")

        if len(results) == 0:
            search_string = click.prompt(
                "No results found. Do you have an ID?",
                type=str,
                default="",
                show_default=False,
            )
            if search_string:
                try:
                    results = [d.release(int(search_string))]
                    logger.info(f"Found {len(results)} results")
                except HTTPError as e:
                    if e.status_code == 404:
                        click.echo("No results found")
                        continue
                    else:
                        raise e
            else:
                continue

        if len(results) > 1:
            click.echo(f"Found {len(results)} results")

            albums = []
            singles = []
            rest = []

            for idx, result in enumerate(results, 1):
                format_ = result.data["format"]
                if "Compilation" in format_:
                    rest.append(result)
                elif (
                    "Album" in format_
                    or "LP" in format_
                    or "EP" in format_
                    or "33 \u2153 RPM" in format_
                ):
                    albums.append(result)
                elif (
                    "Single" in format_
                    or "45 RPM" in format_
                    or "Flexi-disc" in format_
                    or '12"' in format_
                ):
                    singles.append(result)
                elif (
                    "VHS" in format_
                    or "DVD" in format_
                    or "Blu-ray" in format_
                    or "PAL" in format_
                    or "DVDr" in format_
                    or "CDr" in format_
                ):
                    continue
                elif "CD" in format_:
                    rest.append(result)
                else:
                    click.echo(json.dumps(result.data["format"], indent=2))
                    rest.append(result)
                    click.echo("Other")
                if idx > 48:
                    click.echo("Too many results, skipping")
                    break

            prioritised = albums + singles + rest

            for idx, result in enumerate(prioritised, 1):
                click.echo(f"{idx}. {result.title}")

            selected = click.prompt(
                f"Which release? (1-{len(prioritised)})",
                type=str,
                default="",
            )
            if selected == "q":
                break

            if not selected.isdigit():
                results = d.search(search_string, type="master")

                # this is a copy of the above code, TODO refactor
                if len(results) == 0:
                    click.echo("No results found")
                    continue

                if len(results) > 1:
                    click.echo(f"Found {len(results)} results")
                    for idx, result in enumerate(results, 1):
                        click.echo(f"{idx}. {result.title}")

                    selected = click.prompt(
                        f"Which release? (1-{len(results)})",
                        type=str,
                        default="",
                    )
                    if selected == "q":
                        break

                    if not selected.isdigit():
                        continue

            master = prioritised[int(selected) - 1]

        else:
            master = results[0]

        # the discogs library is very weird. It loads some unknown data,
        # then it lazy loads the real data when you first access it. So
        # accessing the title will load the data, and then we can access
        # the rest of the data
        title = master.data["title"]
        release_id = db.upsert_discogs_release(
            DiscogsRelease(
                id=master.id,
                title=title,
                country=master.data["country"],
                genres=sorted(master.genres),
                styles=sorted(master.styles),
                released=master.year,
                uri=master.url,
            )
        )
        logger.debug(f"Created release {release_id}")

        artists_to_add = []
        potential_artists = [artist for artist in master.data["artists"]]
        for artist in potential_artists:
            click.echo(json.dumps(artist, indent=2))
            yes_or_no = click.confirm("Use artist?", default=True, show_default=True)
            if not yes_or_no:
                continue

            artist_obj = d.artist(artist["id"])

            try:
                artists_to_add.append(
                    {
                        "id": artist_obj.id,
                        "name": re.sub(r" \(.*?\)", "", artist_obj.name).strip(),
                        "profile": artist_obj.profile,
                        "uri": artist_obj.url,
                        "role": artist_obj.role,
                    }
                )
            except HTTPError as e:
                if e.status_code == 404:
                    click.echo(f"Weird discog error: {artist['id']} not found")
                    continue

        if not artists_to_add:
            artist_search = click.prompt(
                "Could not find artist, do you want to search manually?",
                type=str,
                default="",
            )
            if not artist_search:
                click.echo("Not searching")
                continue

            potential_artists = d.search(artist_search, type="artist")
            for artist_obj in potential_artists:
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
                        click.echo("Weird discog error: artist not found")
                        continue

        if not artists_to_add:
            click.echo("No artists found, skipping to next release")
            continue

        for artist_obj in artists_to_add:
            db.upsert_discogs_artist(
                record=DiscogsArtist(
                    id=artist_obj["id"],
                    name=artist_obj["name"],
                    profile=artist_obj["profile"],
                    uri=artist_obj["uri"],
                ),
                release_id=release_id,
                role=artist_obj["role"],
            )
            logger.debug(f"Created artist {artist_obj['name']}")

        click.echo(f"This release has {len(master.tracklist)} tracks")

        for idx, track in enumerate(master.tracklist, 1):
            click.echo(f"{idx}. {track.title}")

        selected = click.prompt(
            f"Which track? (1-{len(master.tracklist)})",
            type=str,
            default="",
        )
        if selected == "q":
            break

        if not selected.isdigit():
            continue

        track = master.tracklist[int(selected) - 1].data
        db.upsert_discogs_track(
            record=DiscogsTrack(
                release_id=master.id,
                title=track["title"],
                duration=track["duration"],
                position=track["position"],
                type_=track["type_"],
            ),
            video_id=video_id,
        )

    click.echo(f"Finished {app_context.config}")
