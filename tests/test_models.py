from planitor.models import Minute


def test_minute_entity_mentions():
    minute = Minute(inquiry="Skjal barst frá Veitum ohf. í gær.")
    minute.assign_entity_mentions({"veitur-kennitala": [(16, 27)]})
    assert list(minute.get_inquiry_mention_tokens()) == (
        [
            (None, "Skjal barst frá "),
            ("veitur-kennitala", "Veitum ohf."),
            (None, " í gær."),
        ]
    )
