from .models import (
    Municipality,
    Council,
    CouncilTypeEnum,
    Meeting,
    Entity,
    Case,
    Minute,
)


MUNICIPALITIES_OSM_IDS = {
    # These are `name`, `osm_id` tuples
    "reykjavik_byggingarfulltrui": ("Reykjavík", "2580605"),
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
            council_type=council_type, municipality=municipality, name=council_type.long
        )
        db.add(municipality)
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


def get_geoname_from_address_and_municipality(db, address, municipality):
    # if re.search(r'(\d+)')
    pass


def create_minute(db, meeting, **items):
    case_serial = items.pop("case_serial")
    case_address = items.pop("case_address")
    case, created = get_or_create_case(db, case_serial, meeting.council)

    for items in items.pop("entities", []):
        entity = get_or_create_entity(db, **items)
        if entity not in case.entities:
            case.entities.append(entity)

    minute = Minute(case=case, **items)
    db.add(minute)
    return minute
