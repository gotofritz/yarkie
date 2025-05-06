import logging
from typing import Optional

from tools.config.app_config import YarkieSettings
from tools.data_access.local_db_repository import LocalDBRepository


class AppContext:
    """Holds all the objects needed by commands"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        db: Optional[LocalDBRepository] = None,
    ) -> None:
        self.config = YarkieSettings()
        self.logger = logger or logging.getLogger(__name__)
        self.db = db or LocalDBRepository(config=self.config)

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(name)s:%(levelname)s] %(message)s",
        )
