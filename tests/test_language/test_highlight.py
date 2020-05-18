from planitor.models import Minute
from planitor.language.highlight import (
    get_highlighted_minute_preview,
    explode_wordforms,
)


def test_explode_wordforms():
    print(explode_wordforms("rakaskemmdir"))
    assert explode_wordforms("kjarvalsstaðir högni") == {
        "kjarvalsstöðum",
        "kjarvalsstaða",
        "kjarvalsstaðir",
        "kjarvalsstaði",
        "högni",
        "högna",
    }


def test_get_highlighted_minute_preview():
    minute = Minute(inquiry="kjarvalsstöðum")
    print(list(get_highlighted_minute_preview(minute, "Kjarvalsstaðir")))
