from typing import AsyncIterator, Iterator

from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from starlette.datastructures import Secret

from planitor import config

DB_DSN = config(
    "DATABASE_URL", default="postgresql://planitor:@localhost/planitor", cast=Secret
)


def _get_async_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return dsn
    if dsn.startswith("postgresql+psycopg2://"):
        return dsn.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if dsn.startswith("postgresql://"):
        return dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    return dsn


SQLALCHEMY_ECHO = config("SQLALCHEMY_ECHO", cast=bool, default=False)


engine = create_engine(
    str(DB_DSN),
    connect_args={},
    echo="debug" if SQLALCHEMY_ECHO else False,
    pool_pre_ping=True,
)
async_engine = create_async_engine(
    _get_async_dsn(str(DB_DSN)),
    echo="debug" if SQLALCHEMY_ECHO else False,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, autoflush=False, expire_on_commit=False
)
Base = declarative_base()


def get_db() -> Iterator[Session]:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_context = contextmanager(get_db)


async def get_async_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as db:
        yield db


async_db_context = asynccontextmanager(get_async_db)
