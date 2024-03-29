import asyncio
import datetime as dt
import os

import pytest
import sqlalchemy
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

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

    from planitor import models  # noqa
    from planitor.database import Base, SessionLocal, engine

    assert "planitor_test" in str(engine.url)
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


@pytest.fixture(scope="function", name="emails_message_send")
def emails_message_send_fixture(mocker: MockerFixture):
    return mocker.patch("emails.Message.send")


def _c(db, obj):
    db.add(obj)
    db.commit()
    return obj


@pytest.fixture(scope="function", name="address")
def address_fixture(db, municipality):
    from planitor.models import Address

    address = _c(
        db,
        Address(
            bokst="R",
            byggd=1,
            heiti_nf="Laugavegur",
            heiti_tgf="Laugavegi",
            hnitnum=10018261,
            husnr=151,
            landnr=102866,
            lat_wgs84=64.1432378243864,
            long_wgs84=-21.9093419518678,
            lysing="Hlíðar",
            postnr=105,
            serheiti="",
            stadur_nf="Reykjavík",
            stadur_tgf="Reykjavík",
            svaedi_nf="Höfuðborgarsvæðið",
            svaedi_tgf="Höfuðborgarsvæðinu",
            svfnr=0,
            tegund="Þéttbýli",
            vidsk="151-155",
        ),
    )
    return address


@pytest.fixture(scope="function", name="municipality")
def municipality_fixture(db):
    from planitor.models import Municipality

    municipality = _c(db, Municipality(id=0, name="Reykjavík", slug="reykjavik"))
    return municipality


@pytest.fixture(scope="function", name="case")
def case_fixture(db, address, municipality):
    from planitor.models import Case

    case = _c(db, Case(municipality=municipality, iceaddr=address, serial="foo"))
    return case


@pytest.fixture(scope="function", name="council")
def council_fixture(db, municipality):
    from planitor.models import Council, CouncilTypeEnum

    council = _c(
        db,
        Council(
            name="Building Office",
            municipality=municipality,
            council_type=CouncilTypeEnum.byggingarfulltrui,
        ),
    )
    return council


@pytest.fixture(scope="function", name="meeting")
def meeting_fixture(db, case, council):
    from planitor.models import Meeting

    meeting = _c(db, Meeting(council=council, name="1", start=dt.datetime(2000, 1, 1)))
    return meeting


@pytest.fixture(scope="function", name="minute")
def minute_fixture(db, case, meeting):
    from planitor.models import Minute

    minute = _c(db, Minute(meeting=meeting, case=case, headline="Minute"))
    return minute


@pytest.fixture(scope="function", name="applicant")
def applicant_fixture(db, municipality):
    from planitor.models import Applicant

    applicant = _c(
        db, Applicant(municipality_id=municipality.id, email="foo@bar", serial="foo")
    )
    return applicant


@pytest.fixture(scope="function", name="user")
def user_fixture(db, case, meeting):
    from planitor.models import User

    user = _c(db, User(email="foo@bar.com"))
    return user


@pytest.fixture(scope="function", name="attachment")
def attachment_fixture(db, minute):
    from planitor.models import Attachment

    attachment = _c(db, Attachment(minute=minute, url="foo"))
    return attachment


@pytest.fixture(scope="function", name="company")
def company_fixture(db):
    from planitor.crud import get_or_create_entity
    from planitor.utils.kennitala import Kennitala

    entity, _ = get_or_create_entity(
        db, kennitala=Kennitala("5012131870"), name="Veitur ohf.", address=None
    )
    db.commit()
    return entity


@pytest.fixture(scope="function", name="subscription")
def subscription_fixture(db, user, case):
    from planitor.models import Subscription, SubscriptionTypeEnum

    subscription = _c(
        db, Subscription(case=case, user=user, type=SubscriptionTypeEnum.case)
    )
    return subscription
