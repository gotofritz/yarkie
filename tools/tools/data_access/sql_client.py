import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from tools.orm.schema import Base as Base

metadata = MetaData()


class SQLClient:
    def __init__(self, *, db_url: Path, logger: Optional[logging.Logger] = None):
        self.l = logger or logging.getLogger(__name__)
        db_url = db_url.as_posix()
        self.l.debug(f"Connecting to database at {db_url}")
        self.engine = create_engine(f"sqlite:///{db_url}")
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        metadata.bind = self.engine

    def execute_query(self, query):
        """Execute a SQLAlchemy query and return the results."""
        session = self.Session()
        try:
            result = session.execute(query)
            rows = result.fetchall()
            column_names = result.keys()
            data = [dict(zip(column_names, row)) for row in rows]
            return data
        finally:
            session.close()
