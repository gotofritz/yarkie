"""Service for generating Discogs search strings from video metadata.

This module provides the DiscogsSearchService class, which handles the
business logic for creating search strings from video data to use when
searching for Discogs releases.
"""

import re
from logging import Logger, getLogger
from typing import Optional

from tools.models.models import Video


class DiscogsSearchService:
    """
    Service for generating Discogs search strings from video metadata.

    This service extracts and formats video information (title, uploader,
    description) into optimized search strings for querying the Discogs API.
    """

    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize the DiscogsSearchService.

        Parameters
        ----------
        logger : Optional[Logger], optional
            Logger instance for logging messages, by default None.
        """
        self.logger = logger or getLogger(__name__)

    def generate_search_strings(
        self,
        *,
        title: str,
        uploader: Optional[str] = None,
        description: Optional[str] = None,
    ) -> list[str]:
        """
        Generate search strings from video metadata.

        Takes video metadata and creates multiple search string variations
        that can be used to search for matching Discogs releases. The strings
        are prioritized from most to least specific.

        Parameters
        ----------
        title : str
            The video title.
        uploader : Optional[str], optional
            The video uploader/channel name, by default None.
        description : Optional[str], optional
            The video description, by default None.

        Returns
        -------
        list[str]
            A list of search strings ordered by specificity, with the most
            specific search string first.
        """
        strings: list[str] = []

        # Clean up title by removing text in parentheses and whitespace
        clean_title = re.sub(r" \(.*?\)", "", title).strip()
        strings.append(clean_title)

        # Add uploader-based search string if available
        if uploader:
            # Remove " - Topic" suffix that YouTube adds to official artist channels
            clean_uploader = uploader.replace(" - Topic", "")
            strings.append(f"{clean_title} - {clean_uploader}")

        # Add description-based search string if available
        if description:
            description_lines = description.splitlines()

            # Prefer the 3rd line if available (often contains track info),
            # otherwise use first 64 chars of first line
            if len(description_lines) >= 3:
                desc_text = description_lines[2]
            else:
                desc_text = description_lines[0][:64]

            # Clean up description formatting
            desc_text = desc_text.replace(" · ", " ")

            # Add description in format appropriate to context
            if clean_title in desc_text:
                strings.append(desc_text)
            else:
                strings.append(f"{clean_title} - {desc_text}")

        return strings

    def next_video_to_process(
        self,
        *,
        video: Video,
    ) -> tuple[str, list[str]]:
        """
        Process a video and generate search strings for Discogs lookup.

        Parameters
        ----------
        video : Video
            The video to process.

        Returns
        -------
        tuple[str, list[str]]
            A tuple of (video_id, list of search strings).
        """
        search_strings = self.generate_search_strings(
            title=video.title,
            uploader=video.uploader,
            description=video.description,
        )
        return (video.id, search_strings)
