from planitor.models import Housenumber, Geoname
from planitor.utils.kennitala import Kennitala
from planitor.crud import (
    get_or_create_entity,
    lookup_icelandic_company_in_entities,
    update_case_address,
)


def test_lookup_in_entities(db):
    name = "plúsarkitektar ehf"  # lowercase, missing . at the end
    entity, _ = get_or_create_entity(
        db, Kennitala("6301692919"), name="Plúsarkitektar ehf.", address=""
    )
    db.commit()
    assert lookup_icelandic_company_in_entities(db, name).first() == entity


def tests_geo(db, case):
    geoname = Geoname(osm_id=1, name="Barmahlíð", city="Reykjavík")
    db.add(geoname)
    db.commit()
    housenumber = Housenumber(osm_id=1, housenumber=44, street=geoname)
    db.add(housenumber)
    db.commit()

    case.address = "Barmahlíð 44"
    case.council.municipality.name = "Reykjavík"
    update_case_address(db, case)
    assert case.iceaddr
    assert case.iceaddr.heiti_nf == "Barmahlíð"
    assert case.geoname == geoname
    assert case.housenumber == housenumber
