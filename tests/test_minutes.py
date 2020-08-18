from planitor.models import Minute, Case, CaseEntity, Entity, Response
from planitor.minutes import get_minute_lemmas, get_minute_document, search


def test_get_minute_document(minute):
    minute.headline = "Headline"
    minute.inquiry = "Inquiry"
    minute.remarks = "Remarks."
    minute.case.entities = [CaseEntity(entity=Entity(name="Big Cheese ltd."))]
    minute.responses = [Response(headline="Foo", contents="Bar")]
    assert (
        get_minute_document(minute)
        == """Headline.
Inquiry.
Remarks.
Bar."""
    )


def test_get_minute_lemmas(monkeypatch):
    minute = Minute(remarks="Málinu vísað", case=Case(serial="foo", address="bar"))

    def mock_get_lemmas(text, ignore):
        for fragment in text.split():
            yield fragment

    monkeypatch.setattr(search, "get_lemmas", mock_get_lemmas)
    assert get_minute_lemmas(minute) == [
        "Málinu",
        "er",
        "vísað.",
        "bar",
        "foo",
    ]
