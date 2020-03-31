import os
import asyncio

import sqlalchemy
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "postgresql://planitor:@localhost/planitor_test"


@pytest.fixture(scope="function", name="loop")
def loop_fixture():
    return asyncio.new_event_loop()


@pytest.fixture(scope="session", name="engine")
def engine_fixture() -> sqlalchemy.engine.Engine:
    from planitor.database import engine

    return engine


@pytest.fixture(scope="function", name="db")
def db_fixture(engine):

    from planitor.database import SessionLocal, engine
    from planitor.models import (
        Base,
    )  # Base is also in `database` but this import attaches models

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function", name="app")
def app_fixture(engine):
    app = FastAPI(title="planitor", version="0.0.0")
    return app


@pytest.fixture(scope="function", name="client")
def client_fixture(app):
    client = TestClient(app)
    return client
