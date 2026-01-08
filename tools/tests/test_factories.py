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
from tools.data_access.sql_client import SQLClient, create_sql_client
from tools.services.archiver_service import ArchiverService, create_archiver_service


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
    mock_local_db = MagicMock(spec=LocalDBRepository)

    result = create_archiver_service(local_db=mock_local_db, config=mock_config)

    assert isinstance(result, ArchiverService)
    assert result.local_db == mock_local_db
    assert result.config == mock_config
    assert result.logger is not None


def test_create_archiver_service_with_logger(mock_config: YarkieSettings) -> None:
    """Test create_archiver_service accepts an optional logger."""
    mock_local_db = MagicMock(spec=LocalDBRepository)
    mock_logger = Mock(spec=Logger)

    result = create_archiver_service(
        local_db=mock_local_db, config=mock_config, logger=mock_logger
    )

    assert isinstance(result, ArchiverService)
    assert result.logger == mock_logger
