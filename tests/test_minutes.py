from planitor.minutes import get_minute_document, get_minute_lemmas, search
from planitor.models import Case, CaseEntity, Entity, Minute, Response


def test_get_minute_document(minute):
    print(minute.case.iceaddr)
    minute.headline = "Headline"
    minute.inquiry = "Inquiry"
    minute.remarks = "Remarks."
    minute.case.entities = [CaseEntity(entity=Entity(name="Big Cheese ltd."))]
    minute.responses = [Response(headline="Foo", contents="Bar")]
    assert get_minute_document(minute) == "\n".join(
        ["Headline.", "Inquiry.", "Remarks.", "Bar."]
    )


def test_get_minute_lemmas(monkeypatch, address):
    minute = Minute(
        remarks="Málinu vísað", case=Case(serial="foo", address="bar", iceaddr=address)
    )

    def mock_get_lemmas(text, ignore):
        for fragment in text.split():
            yield fragment

    monkeypatch.setattr(search, "get_lemmas", mock_get_lemmas)
    assert get_minute_lemmas(minute) == [
        "Málinu",
        "er",
        "vísað.",
        "bar",
        "151",
        "151-155",
        "151R",
        "Laugavegi",
        "Laugavegur",
        "foo",
    ]
