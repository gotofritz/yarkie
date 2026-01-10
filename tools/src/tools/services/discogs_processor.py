# tools/services/discogs_processor.py

"""
Discogs processing orchestration service.

This module provides the DiscogsProcessor class, which orchestrates the
multistep workflow for processing videos with Discogs metadata. It separates
business logic from user interaction by accepting an InteractionStrategy.
"""

from logging import Logger, getLogger

from tools.models.processing_models import ProcessingResult
from tools.services.discogs_interaction_strategy import InteractionStrategy
from tools.services.discogs_service import DiscogsService


class DiscogsProcessor:
    """
    Orchestrates Discogs data processing for videos.

    This service coordinates the multistep workflow of searching for,
    selecting, and saving Discogs metadata (releases, artists, tracks)
    for videos. It separates business logic from user interaction by
    delegating all interaction decisions to an InteractionStrategy.

    This design enables:
    - Testing business logic without interactive prompts
    - Multiple interaction implementations (CLI, API, automated)
    - Reusing processing logic across different entry points
    """

    def __init__(
        self,
        *,
        discogs_service: DiscogsService,
        interaction_strategy: InteractionStrategy,
        logger: Logger | None = None,
    ):
        """
        Initialize the DiscogsProcessor.

        Parameters
        ----------
        discogs_service : DiscogsService
            Service for Discogs API interactions and database operations.
        interaction_strategy : InteractionStrategy
            Strategy for handling user interaction decisions.
        logger : Logger | None, optional
            Logger instance for logging messages, by default None.
        """
        self.discogs_service = discogs_service
        self.interaction_strategy = interaction_strategy
        self.logger = logger or getLogger(__name__)

    def process_video(self, *, video_id: str, search_strings: list[str]) -> ProcessingResult:
        """
        Process a single video through the complete Discogs workflow.

        This is the main entry point that orchestrates the entire workflow:
        1. Select search string
        2. Search and select release
        3. Select artists
        4. Select track
        5. Save all metadata

        Parameters
        ----------
        video_id : str
            The ID of the video to process.
        search_strings : list[str]
            Pre-generated search string options for finding releases.

        Returns
        -------
        ProcessingResult
            Result object indicating success/failure, IDs of saved records,
            and any error information.
        """
        # TODO: Implement the main workflow
        return ProcessingResult(
            success=False,
            video_id=video_id,
            message="Not yet implemented",
        )
