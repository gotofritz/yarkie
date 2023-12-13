# tools/models/fakes.py

"""Provide factories for fake versions of models."""
import json
from datetime import datetime

from faker import Faker
from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory

from tools.models.models import Playlist, Video
from tools.data_access.local_db_repository import LocalDBRepository

faker_instance = Faker()


class FakeDBFactory(LocalDBRepository):
    """
    Utility class for generating JSON data to pass to --mock-data.

    This class extends DataRepository and provides methods for building a JSON
    string with mock data for the database.

    Methods:
    --------
    build_json: Generates a JSON string with mock data for the database.
    """

    @classmethod
    def build_json(cls, playlists: Playlist | list[Playlist] | None = None):
        """
        Generate a JSON string with mock data for the DB.

        Args:
        - playlists: If passed, it will be used to populate the 'playlists' table.
        """
        db = {}
        if playlists:
            if isinstance(playlists, list):
                db["playlists"] = [obj.model_dump() for obj in playlists]
            else:
                db["playlists"] = [playlists.model_dump()]
        return json.dumps(db, default=str)


class FakePlaylistFactory(ModelFactory[Playlist]):
    """
    Factory class for Playlist instances with mock data.

    This class uses PolyFactory to generate instances of the Playlist model with
    fake data.

    Attributes:
    - __model__: The Pydantic model class being used (Playlist).
    - __faker__: The Faker instance for generating fake data.

    Example usage:
    --------------
    playlist = FakePlaylistFactory.build()
    """

    __model__ = Playlist
    __faker__ = faker_instance

    title = Use(faker_instance.sentence)
    last_updated = Use(lambda: faker_instance.iso8601(end_datetime=datetime.now()))


class FakeVideoFactory(ModelFactory[Video]):
    """
    Factory class for Video instances with mock data.

    This class uses PolyFactory to generate instances of the Video model with
    fake data.

    Attributes:
    - __model__: The Pydantic model class being used (Video).
    - __faker__: The Faker instance for generating fake data.

    Example usage:
    --------------
    video = FakeVideoFactory.build()
    """

    __model__ = Video
    __faker__ = faker_instance
