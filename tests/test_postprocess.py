from planitor.models import Entity

from planitor.postprocess import _update_minute_with_entity_mentions


def test_update_minute_with_entity_mentions_creates_new_entity(db, minute):
    # Tag
    assert db.query(Entity).count() == 0
    minute.inquiry = "Skjal barst frá Veitum ohf. í gær."
    _update_minute_with_entity_mentions(db, minute)
    assert len(minute.entity_mentions) == 1
    assert len(minute.case.entities) == 1

    # Update should remove case entities
    minute.inquiry = ""
    _update_minute_with_entity_mentions(db, minute)
    assert list(minute.get_inquiry_mention_tokens()) == [(None, "")]
    assert len(minute.entity_mentions) == 0

    # We don’t support chasing down and removing case entities, otherwise this
    # would be zero again.
    assert len(minute.case.entities) == 1

    entity = minute.case.entities[0].entity
    assert entity.slug == "veitur-ohf"
    assert entity.kennitala == "5012131870"


def test_update_minute_with_entity_mentions_uses_existing_entity(db, minute, company):
    # Tag
    assert db.query(Entity).count() == 1
    minute.inquiry = "Skjal barst frá Veitum ohf. í gær."
    _update_minute_with_entity_mentions(db, minute)
    assert list(minute.get_inquiry_mention_tokens())
    assert len(minute.entity_mentions) == 1
    assert minute.case.entities[0].entity == company
    assert db.query(Entity).count() == 1
