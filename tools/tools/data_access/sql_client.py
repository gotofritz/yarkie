import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from tools.orm.schema import Base as Base

metadata = MetaData()


class SQLClient:
    def __init__(self, *, db_url: Path, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug(f"Connecting to database at {db_url}")
        self.engine = create_engine(f"sqlite:///{db_url}")
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def execute_query(self, query: str) -> None:
        """Execute a SQLAlchemy query and return the results as a list of dictionaries."""
        session = self.Session()
        try:
            session.execute(text(query))
        finally:
            session.close()
