from planitor.crud import get_or_create_entity, lookup_icelandic_company_in_entities


def test_lookup_in_entities(db):
    name = "Plúsarkitekta ehf"  # Other inflection, missing . at the end
    entity, _ = get_or_create_entity(db, "", name="Plúsarkitektar ehf.", address="")
    db.commit()
    assert lookup_icelandic_company_in_entities(db, name).first() == (entity, 2)
