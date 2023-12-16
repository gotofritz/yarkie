from pathlib import Path
import pytest
from tools.data_access.file_repository import FileRepository, file_repository


def test_make_thumbnail_path_happy_path(faker, tmp_path):
    """Generate the path for a thumbnail given its key."""

    sut = FileRepository(root=tmp_path)
    key = "A" + faker.word()
    expected_path = tmp_path / "thumbnails/a" / (key + ".webp")
    generated_path = sut.make_thumbnail_path(key=key)


def test_make_video_path_happy_path(faker, tmp_path):
    """Generate the path for a video given its key."""

    sut = FileRepository(root=tmp_path)
    key = "B" + faker.word()
    expected_path = tmp_path / "videos/b" / (key + ".mp4")
    generated_path = sut.make_video_path(key=key)
    assert generated_path == expected_path


@pytest.mark.asyncio()
async def test_write_thumbnail_happy_path(faker, tmp_path):
    """Writes an image file."""

    sut = FileRepository(root=tmp_path)
    key = "C" + faker.word()
    image = faker.image(image_format="webp")
    expected_path = f"{tmp_path}/thumbnails/c/{key}.webp"
    generated_path = await sut.write_thumbnail(key=key, image=image)
    assert generated_path == expected_path

    with open(expected_path, "rb") as file:
        written_image_data = file.read()
    assert written_image_data == image


@pytest.mark.asyncio()
async def test_write_thumbnail_empty(faker, tmp_path):
    """Writes an image file."""

    sut = FileRepository(root=tmp_path)
    key = "E" + faker.word()
    generated_path = await sut.write_thumbnail(key=key)
    assert generated_path == ""


def test_move_video_after_download_happy_path(faker, tmp_path):
    """Writes an image file."""

    sut = FileRepository(root=tmp_path)
    key = "d" + faker.word()

    # it doesn't matter whether it's really a video or not, it's just
    # moved around, there is not attempt at reading it.
    video = faker.image()
    src_folder: Path = tmp_path / faker.word() / faker.word()
    src_folder.mkdir(parents=True, exist_ok=True)
    src_path: Path = src_folder / (key + ".mp4")
    src_path.write_bytes(video)

    expected_path = f"{tmp_path}/videos/d/{key}.mp4"
    generated_path = sut.move_video_after_download(src_path=src_path)
    assert generated_path == expected_path

    with open(expected_path, "rb") as file:
        written_video_data = file.read()
    assert written_video_data == video


def test_file_repository_function():
    """Factory function for FileRepository."""

    sut = file_repository()
    assert isinstance(sut, FileRepository)
