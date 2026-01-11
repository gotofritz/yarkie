"""Provide factories for fake versions of models."""

from datetime import datetime

from faker import Faker
from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory

from tools.models.models import DeletedYoutubeObj, Playlist, Video

faker_instance = Faker()


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
    enabled = True


class FakeVideoFactory(ModelFactory[Video]):
    """
    Factory class for Video instances with mock data.

    This class uses PolyFactory to generate instances of the Video model
    with fake data.

    Attributes: - __model__: The Pydantic model class being used
    (Video).  - __faker__: The Faker instance for generating fake data.

    Example usage:
    --------------
    video = FakeVideoFactory.build()
    """

    __model__ = Video
    __faker__ = faker_instance

    thumbnail = Use(faker_instance.url)


class FakeDeletedVideoFactory(ModelFactory[DeletedYoutubeObj]):
    """
    Factory class for Video instances with mock data.

    This class uses PolyFactory to generate instances of the
    DeletedVideo model with fake data.

    Attributes: - __model__: The Pydantic model class being used
    (DeletedVideo).  - __faker__: The Faker instance for generating fake
    data.

    Example usage:
    --------------
    video = FakeVideoFactory.build()
    """

    __model__ = DeletedYoutubeObj
    __faker__ = faker_instance
