from planitor.models.city import Municipality
from planitor.crud import (
    get_or_create_entity,
    lookup_icelandic_company_in_entities,
    update_case_address,
)
from planitor.models import Geoname, Housenumber
from planitor.utils.kennitala import Kennitala


def test_lookup_in_entities(db):
    name = "plúsarkitektar ehf"  # lowercase, missing . at the end
    entity, _ = get_or_create_entity(
        db, Kennitala("6301692919"), name="Plúsarkitektar ehf.", address=""
    )
    db.commit()
    assert lookup_icelandic_company_in_entities(db, name).first() == entity


def test_geo(db, case):
    geoname = Geoname(osm_id=1, name="Barmahlíð", city="Reykjavík")
    db.add(geoname)
    db.commit()
    housenumber = Housenumber(osm_id=1, housenumber=44, street=geoname)
    db.add(housenumber)
    db.commit()

    case.address = "Barmahlíð 44"
    case.municipality.name = "Reykjavík"
    update_case_address(db, case)
    assert case.iceaddr
    assert case.iceaddr.heiti_nf == "Barmahlíð"
    assert case.geoname == geoname
    assert case.housenumber == housenumber


def test_update_case_address_arborg(db, case):
    municipality = Municipality(id=8200, name="Árborg", slug="arborg")
    db.add(municipality)
    db.commit()
    case.address = "Norðurgata 32"
    case.municipality = municipality
    case.iceaddr = None
    update_case_address(db, case)
    assert case.iceaddr.municipality == municipality


def test_update_case_address_sunnuhvoll(db, case):
    municipality = Municipality(id=8200, name="Árborg", slug="arborg")
    db.add(municipality)
    db.commit()
    case.address = "Sunnuhvoll"
    case.municipality = municipality
    case.iceaddr = None
    # Will pick up Grímsnes- og Grafningshreppur, for whatever reason, but is not in municipality so set to None
    update_case_address(db, case)
    assert case.iceaddr is None
