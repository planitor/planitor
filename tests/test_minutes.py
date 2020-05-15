from planitor.models import Minute, Case
from planitor.minutes import get_minute_lemmas, search


def test_get_minute_lemmas(monkeypatch):
    minute = Minute(remarks="Málinu vísað", case=Case())

    def mock_get_lemmas(text, ignore):
        for fragment in text.split():
            yield fragment

    monkeypatch.setattr(search, "get_lemmas", mock_get_lemmas)
    assert get_minute_lemmas(minute) == "Málinu er vísað".split()
