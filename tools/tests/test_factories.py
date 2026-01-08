# tests/test_factories.py

"""Tests for factory functions that create service instances."""

from logging import Logger
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from tools.config.app_config import YarkieSettings
from tools.data_access.local_db_repository import (
    LocalDBRepository,
    create_local_db_repository,
)
from tools.data_access.playlist_repository import PlaylistRepository
from tools.data_access.sql_client import SQLClient, create_sql_client
from tools.data_access.video_repository import VideoRepository
from tools.services.archiver_service import ArchiverService, create_archiver_service
from tools.services.video_sync_service import VideoSyncService


def test_create_sql_client_with_config(mock_config: YarkieSettings) -> None:
    """Test create_sql_client creates a SQLClient with the given config."""
    result = create_sql_client(config=mock_config)

    assert isinstance(result, SQLClient)
    assert result.logger is not None


def test_create_sql_client_with_logger(mock_config: YarkieSettings) -> None:
    """Test create_sql_client accepts an optional logger."""
    mock_logger = Mock(spec=Logger)

    result = create_sql_client(config=mock_config, logger=mock_logger)

    assert isinstance(result, SQLClient)
    assert result.logger == mock_logger


def test_create_local_db_repository_with_dependencies(
    sql_client: SQLClient, mock_config: YarkieSettings
) -> None:
    """Test create_local_db_repository creates a LocalDBRepository."""
    result = create_local_db_repository(sql_client=sql_client, config=mock_config)

    assert isinstance(result, LocalDBRepository)
    assert result.sql_client == sql_client
    assert result.config == mock_config
    assert result.logger is not None


def test_create_local_db_repository_with_logger(
    sql_client: SQLClient, mock_config: YarkieSettings
) -> None:
    """Test create_local_db_repository accepts an optional logger."""
    mock_logger = Mock(spec=Logger)

    result = create_local_db_repository(
        sql_client=sql_client, config=mock_config, logger=mock_logger
    )

    assert isinstance(result, LocalDBRepository)
    assert result.logger == mock_logger


def test_create_archiver_service_with_dependencies(mock_config: YarkieSettings) -> None:
    """Test create_archiver_service creates an ArchiverService."""
    mock_playlist_repo = MagicMock(spec=PlaylistRepository)
    mock_video_repo = MagicMock(spec=VideoRepository)
    mock_sync_service = MagicMock(spec=VideoSyncService)

    result = create_archiver_service(
        playlist_repository=mock_playlist_repo,
        video_repository=mock_video_repo,
        sync_service=mock_sync_service,
        config=mock_config,
    )

    assert isinstance(result, ArchiverService)
    assert result.playlist_repository == mock_playlist_repo
    assert result.video_repository == mock_video_repo
    assert result.sync_service == mock_sync_service
    assert result.config == mock_config
    assert result.logger is not None


def test_create_archiver_service_with_logger(mock_config: YarkieSettings) -> None:
    """Test create_archiver_service accepts an optional logger."""
    mock_playlist_repo = MagicMock(spec=PlaylistRepository)
    mock_video_repo = MagicMock(spec=VideoRepository)
    mock_sync_service = MagicMock(spec=VideoSyncService)
    mock_logger = Mock(spec=Logger)

    result = create_archiver_service(
        playlist_repository=mock_playlist_repo,
        video_repository=mock_video_repo,
        sync_service=mock_sync_service,
        config=mock_config,
        logger=mock_logger,
    )

    assert isinstance(result, ArchiverService)
    assert result.logger == mock_logger
