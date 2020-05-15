import re
from typing import Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from planitor.cases import get_case_status_from_remarks
from planitor.language.companies import clean_company_name
from planitor.models import (
    Case,
    CaseEntity,
    Council,
    CouncilTypeEnum,
    Entity,
    EntityTypeEnum,
    Geoname,
    Housenumber,
    Meeting,
    Minute,
    Municipality,
)
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
    db, kennitala: Kennitala, name: str, address: str
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


""" The following regex matches street and house numbers like these:
Síðumúli 24-26
Prófgata 12b-14b
Sæmundargata 21
Tjarnargata 10D
Bauganes 3A
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

    case, case_created = get_or_create_case(db, case_serial, meeting.council)
    case.address = case_address

    if case_created:
        (
            case.geoname,
            case.housenumber,
        ) = get_geoname_and_housenumber_from_address_and_municipality(
            db, address=case_address, municipality=meeting.council.municipality,
        )
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

    db.add(minute)
    return minute


def get_search_results(db: Session, search_query: str):
    tsvector = func.to_tsvector("simple", Minute.lemmas)
    tsquery = func.websearch_to_tsquery("simple", search_query)
    sa_query = (
        db.query(Minute)
        .filter(tsvector.op("@@")(tsquery))
        .order_by(func.ts_rank(tsvector, tsquery))
    )
    return sa_query


def update_case_status(db, case):
    """ Query minutes in chronological meeting order, the last minute status will
    become the case status.

    """
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
