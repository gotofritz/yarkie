import logging

from tools.config.app_config import YarkieSettings
from tools.data_access.local_db_repository import LocalDBRepository


class AppContext:
    """Holds all the objects needed by commands."""

    def __init__(
        self,
        *,
        config: YarkieSettings,
        logger: logging.Logger,
        db: LocalDBRepository,
    ) -> None:
        """Initialize AppContext with injected dependencies.

        Parameters
        ----------
        config : YarkieSettings
            The application configuration.
        logger : logging.Logger
            The logger instance.
        db : LocalDBRepository
            The local database repository.
        """
        self.config = config
        self.logger = logger
        self.db = db

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(name)s:%(levelname)s] %(message)s",
        )
