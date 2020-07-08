import datetime as dt
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

    from planitor.database import SessionLocal, engine, Base
    from planitor import models  # noqa

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


def _c(db, obj):
    db.add(obj)
    db.commit()
    return obj


@pytest.fixture(scope="function", name="case")
def case_fixture(db):
    from planitor.models import Municipality, Council, Case

    muni = _c(db, Municipality(name="Acropolis", slug="acropolis"))
    council = _c(db, Council(name="Building Office", municipality=muni))
    case = _c(db, Case(council=council))
    return case


@pytest.fixture(scope="function", name="meeting")
def meeting_fixture(db, case):
    from planitor.models import Meeting

    meeting = _c(
        db, Meeting(council=case.council, name="1", start=dt.datetime(2000, 1, 1))
    )
    return meeting


@pytest.fixture(scope="function", name="minute")
def minute_fixture(db, case, meeting):
    from planitor.models import Minute

    minute = _c(db, Minute(meeting=meeting, case=case))
    return minute


@pytest.fixture(scope="function", name="attachment")
def attachment_fixture(db, minute):
    from planitor.models import Attachment

    attachment = _c(db, Attachment(minute=minute, url="foo"))
    return attachment


@pytest.fixture(scope="function", name="company")
def company_fixture(db):
    from planitor.crud import get_or_create_entity
    from planitor.utils.kennitala import Kennitala

    entity, created = get_or_create_entity(
        db, kennitala=Kennitala("5012131870"), name="Veitur ohf.", address=None
    )
    db.commit()
    return entity
