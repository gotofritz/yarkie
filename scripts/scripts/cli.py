import pickle
from typing import Any
import click
from pathlib import Path, PosixPath
import json
from pydantic import BaseModel, Field
from sqlite_utils import Database
from yt_dlp import YoutubeDL
from datetime import datetime
import shutil
import requests

FG_ERROR = "red"
FG_SECTION = "blue"
INDENT = 4 * " "

ROOT = Path(__file__).parent.parent.parent / "data"
DB_FILE = ROOT / "yarkie.db"
VIDEO_ROOT = ROOT / "videos"
THUMBNAIL_ROOT = ROOT / "thumbnails"


class VideoLogger:
    @staticmethod
    def downloading(d):
        """Progress hook for video downloading"""
        # Get video's id
        id = d["info_dict"]["id"]

        # Downloading percent
        if d["status"] == "downloading":
            percent = d["_percent_str"].strip()
            print(
                f"  • Downloading {id}, at {percent}..                ",
                end="\r",
            )

        # Finished a video's download
        elif d["status"] == "finished":
            print(f"  • Downloaded {id}        ")

    def debug(self, msg):
        """Debug log messages, ignored"""
        pass

    def info(self, msg):
        """Info log messages ignored"""
        pass

    def warning(self, msg):
        """Warning log messages ignored"""
        pass

    def error(self, msg):
        """Error log messages"""
        pass


ydl_settings = {
    # Centralized logging system; makes output fully quiet
    "logger": VideoLogger(),
    # Skip downloading pending livestreams (#60 <https://github.com/Owez/yark/issues/60>)
    "ignore_no_formats_error": True,
    # Concurrent fragment downloading for increased resilience (#109 <https://github.com/Owez/yark/issues/109>)
    "concurrent_fragment_downloads": 8,
}


class VideoRecord(BaseModel):
    id: str
    playlist_id: str
    title: str
    description: str = Field(default="")
    uploader: str = Field(default="")
    duration: float = 0
    view_count: int = 0
    comment_count: int = 0
    like_count: int = Field(default=0)
    upload_date: str = 0
    width: int = 0
    height: int = 0
    video_file: str = ""
    thumbnail: str = ""
    deleted: bool = Field(default=False)
    last_updated: datetime = Field(default_factory=datetime.now)

    @classmethod
    def model_validate_yark_object(
        cls, yark_object: dict[str, Any], playlist_id: str, local_path: Path
    ) -> "VideoRecord":
        """Convert a yark object into one of these"""

        def pick_latest(obj: dict[str, Any], default: Any = ""):
            """
            Yark stores objects in this strange way, { date1: value1,
            date2: value2 ...}. This method picks the latest value.
            """
            key = sorted(obj.keys(), reverse=True)[0]
            return obj[key] or default

        return cls(
            id=yark_object["id"],
            playlist_id=playlist_id,
            title=pick_latest(yark_object["title"]),
            description=pick_latest(yark_object["description"]),
            view_count=pick_latest(yark_object["views"], 0),
            like_count=pick_latest(yark_object["likes"], 0),
            upload_date=yark_object["uploaded"],
            width=yark_object["width"],
            height=yark_object["height"],
            thumbnail=pick_latest(yark_object["thumbnail"]),
            video_file=(
                local_path / "videos" / (yark_object["id"] + ".mp4")
            ).as_posix(),
            deleted=pick_latest(yark_object["deleted"], False),
        )


def _yark_obj_to_table(yark_obj: dict[str, str]):
    """Creates a dict from a yark file, for easy look up."""


@click.group()
@click.version_option()
def cli():
    "helpers and set up scripts for yarkie"


@cli.command(name="command")
def first_command():
    "Command description goes here"
    url = "https://www.youtube.com/watch?v=HWMsWO0vPa8"
    with YoutubeDL(ydl_settings) as ydl:
        res: dict[str, Any] = ydl.extract_info(url, download=False)
        click.echo(f"{INDENT}{json.dumps(res, indent=2)}")


@cli.command(name="migrate")
@click.argument(
    "paths",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=False,
        readable=True,
        path_type=Path,
    ),
)
@click.option(
    "-o",
    "--option",
    help="An example option",
)
def migrate(paths, option):
    """Migrate information from yark folders (without moving videos)."""

    db: Database
    try:
        db = Database(DB_FILE, recreate=False)
    except Exception as e:
        click.secho(f"Error opening DB {DB_FILE}: {e}:", fg=FG_ERROR)
        exit(1)

    in_memory_store: dict[str, VideoRecord] = {}
    download_queue: list[VideoRecord] = []
    records = []
    for i, path in enumerate(paths):
        for entry in path.iterdir():
            if (
                not entry.is_dir()
                # or entry.name == "bass-classic-03"
                # or entry.name == "music-my-kind"
            ):
                continue
            yark_file = entry / "yark.json"
            if not yark_file.exists():
                click.secho(f"No json file found: {yark_file}:", fg=FG_ERROR)
                continue
            click.echo(f"Loading: {yark_file}:")

            settings: dict[str, Any]
            try:
                # load yark file
                settings = json.loads(yark_file.read_text())
                _, playlist_id = settings["url"].split("?list=")

                # extract video infos and store in memory db
                for video_info in settings["videos"]:
                    video_record = VideoRecord.model_validate_yark_object(
                        yark_object=video_info,
                        playlist_id=playlist_id,
                        local_path=entry.resolve(),
                    )
                    in_memory_store[video_record.id] = video_record

            except Exception as exc:
                click.secho(
                    f"Problems reading json file: {exc}: {video_info}", fg=FG_ERROR
                )
                continue

            with YoutubeDL(ydl_settings) as ydl:
                click.echo(f"{INDENT}Querying Youtube...")
                playlist_info: dict[str, Any] = ydl.extract_info(
                    settings["url"], download=False
                )
                playlist_record: dict[str, Any] = {
                    "id": playlist_info["id"],
                    "title": playlist_info["title"],
                    "description": playlist_info["description"],
                    "last_updated": datetime.now(),
                }
                db["playlists"].upsert(playlist_record, pk="id")
                with open(Path(".") / (entry.name + ".json"), "w") as file:
                    json.dump(playlist_info, fp=file, indent=2)
                click.echo(
                    f"{INDENT}Upserted playlist: {json.dumps(playlist_record, indent=2, default=str)} and dumped to "
                    + (Path(".") / (entry.name + ".json")).as_posix()
                )

                # get videos info from YT
                for video_info in playlist_info["entries"]:
                    for field in ["comment_count", "like_count", "view_count"]:
                        if field not in video_info or video_info[field] is None:
                            video_info[field] = 0
                    try:
                        video_record = VideoRecord.model_validate(video_info)
                        # update local record
                        if video_record.id in in_memory_store:
                            id = video_record.id
                            # assets are already stored locally
                            video_record.thumbnail = in_memory_store[id].thumbnail
                            video_record.video_file = in_memory_store[id].video_file
                            in_memory_store[id] = video_record

                        # will deal with it later
                        else:
                            download_queue.append(video_record)
                    except Exception as e:
                        click.secho(f"{INDENT}Error {e} with {video_info}", fg=FG_ERROR)
                        if video_record.id in in_memory_store:
                            in_memory_store[id].deleted = True

                click.echo(
                    f"{INDENT}Found {len(playlist_info['entries'])} videos. Download queue is now {len(download_queue)}"
                )

        for record in download_queue:
            image = requests.get(record.thumbnail).content
            dest_folder = THUMBNAIL_ROOT / record.id[0:2]
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest = dest_folder / (record.id + ".webp")
            with open(dest, "wb+") as file:
                file.write(image)
                click.echo(
                    f"{INDENT}{INDENT}Downloading thumbnail for {record.title} {dest}"
                )
                record.thumbnail = dest

            dest_folder = VIDEO_ROOT / record.id[0:2]
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest = dest_folder / (record.id + ".mp4")
            settings = {
                # Set the output path
                "outtmpl": f"{dest_folder}/%(id)s.%(ext)s",
                # Centralized logger hook for ignoring all stdout
                "logger": VideoLogger(),
                # Logger hook for download progress
                "progress_hooks": [VideoLogger.downloading],
                "format": "mp4",
            }
            with YoutubeDL(settings) as ydl:
                try:
                    if not dest.exists():
                        click.echo(
                            f"{INDENT}{INDENT}Downloading video for {record.title} {dest}"
                        )
                        ydl.download([record.id])
                    record.video_file = dest
                    in_memory_store[record.id] = record
                except Exception as e:
                    click.secho(
                        f"{INDENT}{INDENT}Downloading failed {e}", color=FG_ERROR
                    )

        click.echo(f"{INDENT}Copying local files")
        for record in in_memory_store.values():
            dest_folder = VIDEO_ROOT / record.id[0:2]
            dest = dest_folder / (record.id + ".mp4")
            if not dest.exists():
                dest_folder.mkdir(parents=True, exist_ok=True)
                shutil.copy(record.video_file, dest)
                click.echo(f"{INDENT}{INDENT}Copying {dest}")
            record.video_file = dest.as_posix()

            dest_folder = THUMBNAIL_ROOT / record.id[0:2]
            dest = dest_folder / (record.id + ".webp")
            if not dest.exists():
                dest_folder.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy(
                        entry.resolve() / "thumbnails" / (record.thumbnail + ".webp"),
                        dest,
                    )
                    click.echo(f"{INDENT}{INDENT}Copying {dest}")
                except Exception as e:
                    click.echo(f"{INDENT}{INDENT}Could not copy {dest}: {e}")
            record.thumbnail = dest.as_posix()

            records.append(record.model_dump())

        with open("records.pickle", "wb") as f:
            pickle.dump(records, f)

        table = db["videos"].upsert_all(
            records=records, pk="id", foreign_keys=["playlist_id"]
        )
        click.echo(f"UPSERTED {len(records)} records, {table}")

        click.echo(f"DONE")
