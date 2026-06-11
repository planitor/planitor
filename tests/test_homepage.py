import datetime as dt
import os

from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-secret")

from planitor.main import app


def test_municipalities_index_renders_fresh_case_relationships(db, case, meeting):
    case.created = dt.datetime.utcnow()
    case.headline = "Fresh planning case"
    db.commit()

    response = TestClient(app).get("/s")

    assert response.status_code == 200
    assert "Fresh planning case" in response.text
    assert "Laugavegur" in response.text
