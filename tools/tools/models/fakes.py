from datetime import datetime
import json
from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from faker import Faker
from tools.repositories import DataRepository
from tools.models.models import Playlist, Video

faker_instance = Faker()


class FakeDBFactory(DataRepository):
    @classmethod
    def build_json(cls, playlists: Playlist | list[Playlist] | None = None):
        db = {}
        if playlists:
            if isinstance(playlists, list):
                db["playlists"] = [obj.model_dump() for obj in playlists]
            else:
                db["playlists"] = [playlists.model_dump()]
        return json.dumps(db, default=str)


class FakePlaylistFactory(ModelFactory[Playlist]):
    __model__ = Playlist
    __faker__ = faker_instance

    title = Use(faker_instance.sentence)
    last_updated = Use(lambda: faker_instance.iso8601(end_datetime=datetime.now()))


class FakeVideoFactory(ModelFactory[Video]):
    __model__ = Video
    __faker__ = faker_instance
