# tools/models/fakes.py

"""Provide factories for fake versions of models."""

import json

from faker import Faker

from tools.models.models import Playlist, Video

faker_instance = Faker()


class FakeDBFactory:
    """
    Utility class for generating JSON data to pass to --mock-data.

    This class provides methods for building a JSON string with mock data
    for the database.

    Methods:
    --------
    build_json: Generates a JSON string with mock data for the database.
    """

    @classmethod
    def build_json(
        cls,
        playlists: Playlist | list[Playlist] | None = None,
        videos: Video | list[Video] | None = None,
    ) -> str:
        """
        Generate a JSON string with mock data for the DB.

        Args:
        - playlists: If passed, it will be used to populate the 'playlists' table.
        - videos: If passed, it will be used to populate the 'videos' table.
        """
        db = {}
        if playlists:
            if isinstance(playlists, list):
                db["playlists"] = [obj.model_dump() for obj in playlists]
            else:
                db["playlists"] = [playlists.model_dump()]
        if videos:
            if isinstance(videos, list):
                db["videos"] = [obj.model_dump() for obj in videos]
            else:
                db["videos"] = [videos.model_dump()]
        return json.dumps(db, default=str)
