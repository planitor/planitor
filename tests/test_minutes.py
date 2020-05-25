from planitor.models import Minute, Case, CaseEntity, Entity
from planitor.minutes import get_minute_lemmas, get_minute_document, search


def test_get_minute_document(minute):
    minute.inquiry = "foo"
    minute.case.entities = [CaseEntity(entity=Entity(name="bar"))]
    assert get_minute_document(minute) == "foo\nbar"


def test_get_minute_lemmas(monkeypatch):
    minute = Minute(remarks="Málinu vísað", case=Case())

    def mock_get_lemmas(text, ignore):
        for fragment in text.split():
            yield fragment

    monkeypatch.setattr(search, "get_lemmas", mock_get_lemmas)
    assert get_minute_lemmas(minute) == "Málinu er vísað".split()
