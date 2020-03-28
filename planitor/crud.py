import re

from .models import (
    Municipality,
    Council,
    CouncilTypeEnum,
    Meeting,
    Entity,
    Case,
    Minute,
    Housenumber,
    Geoname,
    CaseTag,
    Tag,
)


MUNICIPALITIES_OSM_IDS = {
    # These are `name`, `osm_id` tuples
    "reykjavik": ("Reykjavík", "2580605"),
}


def get_or_create_municipality(db, slug):
    name, osm_id = MUNICIPALITIES_OSM_IDS[slug]
    muni = db.query(Municipality).filter_by(geoname_osm_id=osm_id).first()
    created = False
    if muni is None:
        muni = Municipality(name=name, geoname_osm_id=osm_id)
        db.add(muni)
        created = True
    return muni, created


def get_or_create_council(db, municipality, slug):
    council_type = getattr(CouncilTypeEnum, slug)
    created = False
    council = (
        db.query(Council)
        .filter_by(council_type=council_type, municipality=municipality)
        .first()
    )
    if council is None:
        council = Council(
            council_type=council_type,
            municipality=municipality,
            name=council_type.value["long"],
        )
        db.add(council)
        created = True
    return council, created


def get_or_create_meeting(db, council, name):
    meeting = db.query(Meeting).filter_by(council=council, name=name).first()
    created = False
    if meeting is None:
        meeting = Meeting(council=council, name=name)
        db.add(meeting)
        created = True
    return meeting, created


def get_or_create_entity(db, kennitala, name, address):
    entity = db.query(Entity).filter_by(kennitala=kennitala).first()
    created = False
    if entity is None:
        entity = Entity(kennitala=kennitala, name=name)
        db.add(entity)
        created = True
    return entity, created


def get_or_create_case(db, serial, council):
    case = db.query(Case).filter_by(serial=serial, council=council).first()
    created = False
    if case is None:
        case = Case(serial=serial, council=council)
        db.add(case)
        created = True
    return case, created


""" The following regex matches street and house numbers like these:

Síðumúli 24-26
Prófgata 12b-14b
Sæmundargata 21
Tjarnargata 10D
Hallgerðargata 19B
Bauganes 3A
Síðumúli 24 - 26
Vesturás 10 - 16

"""

ADDRESS_RE = re.compile(r"^([^\W\d]+) (\d+[A-Za-z]?(?: ?- ?)?(?:\d+[A-Za-z]?)?)?$")


def get_geoname_and_housenumber_from_address_and_municipality(
    db, address, municipality
):
    match = re.match(ADDRESS_RE, address)
    if not match:
        return None, None

    street_name, number = match.groups()
    street = (
        db.query(Geoname)
        .filter_by(name=street_name, city=municipality.name)
        .order_by(Geoname.importance)
        .first()
    )

    if street is None:
        return None, None

    housenumber = (
        db.query(Housenumber)
        .filter_by(street=street, housenumber=number.replace(" ", ""))
        .first()
    )
    return street, housenumber


def create_minute(db, meeting, **items):
    case_serial = items.pop("case_serial")
    case_address = items.pop("case_address")

    case, created = get_or_create_case(db, case_serial, meeting.council)
    case.address = case_address

    if created:
        (
            case.geoname,
            case.housenumber,
        ) = get_geoname_and_housenumber_from_address_and_municipality(
            db, address=case_address, municipality=meeting.council.municipality,
        )
        db.add(case)

    minute = Minute(case=case, meeting=meeting, **items)
    db.add(minute)
    return minute


def get_or_create_tag(db, name):
    tag = db.query(Tag).filter_by(name=name).first()
    created = False
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        created = True
    return tag, created


def get_or_create_case_tag(db, tag, case):
    case_tag = db.query(CaseTag).filter_by(tag_id=tag.name, case_id=case.id).first()
    created = False
    if case_tag is None:
        case_tag = CaseTag(case_id=case.id, tag_id=tag.name)
        db.add(case_tag)
        created = True
    return case_tag, created
