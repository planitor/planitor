from typing import Tuple, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from planitor.cases import get_case_status_from_remarks
from planitor.language.companies import clean_company_name
from planitor.models import (
    Address,
    Case,
    CaseEntity,
    Council,
    CouncilTypeEnum,
    Entity,
    EntityTypeEnum,
    Meeting,
    Geoname,
    Housenumber,
    Minute,
    Municipality,
)
from planitor.geo import get_address_lookup_params, lookup_address
from planitor.utils.kennitala import Kennitala
from planitor.utils.text import slugify, fold

MUNICIPALITIES_OSM_IDS = {
    # These are `name`, `osm_id` tuples
    "reykjavik": ("Reykjavík", "2580605"),
}


def get_or_create_municipality(db, slug):
    name, osm_id = MUNICIPALITIES_OSM_IDS[slug]
    muni = db.query(Municipality).filter_by(geoname_osm_id=osm_id).first()
    created = False
    if muni is None:
        muni = Municipality(name=name, geoname_osm_id=osm_id, slug=slug)
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


def get_or_create_entity(
    db, kennitala: Kennitala, name: str, address: Optional[str]
) -> Tuple[Entity, bool]:
    entity = db.query(Entity).filter_by(kennitala=kennitala.kennitala).first()
    created = False
    if entity is None:
        entity_type = (
            EntityTypeEnum.person if kennitala.is_person() else EntityTypeEnum.company
        )
        if entity_type == EntityTypeEnum.company:
            name = clean_company_name(name)
        entity = Entity(
            kennitala=kennitala.only_digits(),
            name=name,
            address=address,
            slug=slugify(name),
            entity_type=entity_type,
            birthday=kennitala.get_birth_date(),
        )
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


def get_or_create_case_entity(db: Session, case: Case, entity: Entity, applicant: bool):
    case_entity = (
        db.query(CaseEntity)
        .filter_by(entity_id=entity.kennitala, case_id=case.id)
        .first()
    )
    created = False
    if case_entity is None:
        case_entity = CaseEntity(case_id=case.id, entity=entity, applicant=applicant)
        db.add(case_entity)
        created = True
    else:
        if applicant:
            case_entity.applicant = applicant
            db.add(case_entity)
    return case_entity, created


def create_minute(db, meeting, **items):
    case_serial = items.pop("case_serial")
    case_address = items.pop("case_address")

    case, case_created = get_or_create_case(db, case_serial, meeting.council)
    case.address = case_address

    if case_created:
        update_case_address(db, case)
        case.updated = meeting.start
        db.add(case)

    minute = Minute(case=case, meeting=meeting, **items)

    # The wording of the minute remarks tells us the case status
    status = get_case_status_from_remarks(minute.remarks)
    minute.status = status

    # Also persist this status on the case unless a more recent meeting with the case
    # has been held
    if case_created or case.updated < meeting.start:
        case.status = minute.status
        case.updated = meeting.start
        case.headline = meeting.headline

    db.add(minute)
    return minute


# Just to be careful, list the keys we are interested in in case iceaddr adds new fields
# which would not yet be columns on our side - in addition to dropping the x_isn93,
# y_isn93 fields.
ADDRESS_KEYS = [
    "hnitnum",
    "bokst",
    "byggd",
    "heiti_nf",
    "heiti_tgf",
    "husnr",
    "landnr",
    "lat_wgs84",
    "long_wgs84",
    "lysing",
    "postnr",
    "serheiti",
    "stadur_nf",
    "stadur_tgf",
    "svaedi_nf",
    "svaedi_tgf",
    "svfnr",
    "tegund",
    "vidsk",
]


def get_or_create_address(db, iceaddr_match):
    address = db.query(Address).get(iceaddr_match["hnitnum"])
    if address is None:
        address = Address(**{k: v for k, v in iceaddr_match.items() if k in ADDRESS_KEYS})
        db.add(address)
        db.commit()
    return address


def get_geoname_and_housenumber(db, street, number, letter, city):

    street = (
        db.query(Geoname)
        .filter_by(name=street, city=city)
        .order_by(Geoname.importance)
        .first()
    )

    if street is None:
        return None, None

    housenumber = (
        db.query(Housenumber)
        .filter(Housenumber.street == street)
        .filter(
            (Housenumber.housenumber == f"{number}{letter}")
            | (Housenumber.housenumber == str(number))
        )
        .first()
    )

    return street, housenumber


def update_case_address(db, case):
    """ Update the iceaddr, geoname and housenumber attributes. There is significant
    overlaps between iceaddr and geoname functionality but good to have both.

    """
    city = case.council.municipality.name
    street, number, letter = get_address_lookup_params(case.address)

    iceaddr_match = lookup_address(street, number, letter, city)
    if iceaddr_match:
        address = get_or_create_address(db, iceaddr_match)
        case.iceaddr = address

    geoname, housenumber = get_geoname_and_housenumber(db, street, number, letter, city)
    case.geoname, case.housenumber = geoname, housenumber

    db.add(case)
    db.commit()


def update_case_status(db, case):
    """ Query minutes in chronological meeting order, the last minute status will
    become the case status.

    """
    status = None
    for minute in (
        db.query(Minute)
        .join(Meeting)
        .join(Case)
        .filter(Minute.case == case)
        .order_by(Meeting.start)
    ):
        status = get_case_status_from_remarks(minute.remarks)
        minute.status = status
        db.add(minute)
    case.status = status
    db.add(case)


def lookup_icelandic_company_in_entities(db, name):
    name = clean_company_name(name).lower()
    return db.query(Entity).filter(
        Entity.entity_type == EntityTypeEnum.company, func.lower(Entity.name) == name,
    )


MAX_LEVENSHTEIN_DISTANCE = 5


def levenshtein_company_lookup(db, name, max_distance=MAX_LEVENSHTEIN_DISTANCE):
    """ As described above, we may encounter similar looking inflections of company
    names. Instead of tokenizing and lemming words (which we could ...) we just use a
    simple Levenshtein distance calculation. This will also be useful for search.

    Here we use ascii folding and rely on the slug column which is also ascii folded.
    This is also useful for quick ranking of results for typing inputs that doesn’t
    require capital letters or accented characters.

    """

    folded = clean_company_name(fold(name))
    col = func.levenshtein_less_equal(Entity.slug, folded, max_distance)
    return db.query(Entity, col).filter(col <= max_distance).order_by(col)
