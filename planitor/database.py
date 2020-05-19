from contextlib import contextmanager
from threading import Semaphore

import dramatiq
import psycopg2
from dramatiq_pg import PostgresBroker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import register_composites
from starlette.datastructures import Secret

from planitor import config

DB_DSN = config(
    "DATABASE_URL", default="postgresql://planitor:@localhost/planitor", cast=Secret
)

engine = create_engine(str(DB_DSN), connect_args={})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    try:
        db = SessionLocal()
        register_composites(db.connection())
        yield db
    finally:
        db.close()


db_context = contextmanager(get_db)


class ReallyThreadedConnectionPool(psycopg2.pool.ThreadedConnectionPool):
    """
    https://stackoverflow.com/a/53437049
    """

    def __init__(self, minconn, maxconn, *args, **kwargs):
        self._semaphore = Semaphore(maxconn)
        super().__init__(minconn, maxconn, *args, **kwargs)

    def getconn(self, *args, **kwargs):
        self._semaphore.acquire()
        return super().getconn(*args, **kwargs)

    def putconn(self, *args, **kwargs):
        super().putconn(*args, **kwargs)
        self._semaphore.release()


pool = ReallyThreadedConnectionPool(minconn=0, maxconn=4, dsn=str(DB_DSN))
broker = PostgresBroker(pool=pool)
dramatiq.set_broker(broker)
