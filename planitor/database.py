import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import register_composites

SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://planitor:@localhost/planitor"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    try:
        db = SessionLocal()
        register_composites(db.connection())
        yield db
    finally:
        db.close()
