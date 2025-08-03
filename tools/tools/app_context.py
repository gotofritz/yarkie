import logging
from typing import Optional

from tools.config.app_config import YarkieSettings
from tools.data_access.local_db_repository import LocalDBRepository
from tools.data_access.sql_client import SQLClient


class AppContext:
    """Holds all the objects needed by commands"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        db: Optional[LocalDBRepository] = None,
    ) -> None:
        self.config = YarkieSettings()
        self.logger = logger or logging.getLogger(__name__)
        sql_client = SQLClient(db_url=self.config.db_path)
        self.db = db or LocalDBRepository(
            sql_client=sql_client, logger=self.logger, config=self.config
        )

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(name)s:%(levelname)s] %(message)s",
        )
