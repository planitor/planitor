from contextlib import contextmanager

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
