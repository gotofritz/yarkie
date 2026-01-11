"""Pydantic models for processing results and workflows."""

from pydantic import BaseModel, Field


class ProcessingResult(BaseModel):
    """
    Result of processing a video through the Discogs workflow.

    This model encapsulates the outcome of attempting to process a video,
    including success/failure status, identifiers of created/updated records,
    and any error information.

    Attributes
    ----------
    success : bool
        Whether the processing completed successfully.
    video_id : str
        The ID of the video that was processed.
    message : str
        Human-readable message describing the outcome.
    release_id : int | None
        The Discogs release ID that was saved, if any.
    artist_ids : list[int]
        List of Discogs artist IDs that were saved.
    track_id : int | None
        The Discogs track ID that was saved, if any.
    error : str | None
        Error message if processing failed, None otherwise.
    """

    success: bool
    video_id: str
    message: str
    release_id: int | None = None
    artist_ids: list[int] = Field(default_factory=list)
    track_id: int | None = None
    error: str | None = None
