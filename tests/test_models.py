from planitor.models import Minute
from planitor.utils.kennitala import Kennitala


def test_minute_entity_mentions():
    minute = Minute(inquiry="Skjal barst loksins frá Veitum ohf. í gær.")
    minute.assign_entity_mentions({"5301170490": [(24, 35)]})
    assert [
        ((k.kennitala if isinstance(k, Kennitala) else None), j)
        for k, j in minute.get_inquiry_mention_tokens()
    ] == (
        [
            (None, "Skjal barst loksins frá "),
            ("5301170490", "Veitum ohf."),
            (None, " í gær."),
        ]
    )
