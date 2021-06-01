from typing import Optional, Tuple, NamedTuple

from iceaddr import iceaddr_lookup, iceaddr_suggest
from iceaddr.addresses import _run_addr_query
from sqlalchemy import func
from sqlalchemy.orm import Session

from planitor.cases import get_case_status_from_remarks
from planitor.geo import get_address_lookup_params, lookup_address
from planitor.language.companies import (
    clean_company_name,
    yield_entity_name_search_tokens,
)
from planitor.models import (
    Address,
    Attachment,
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
from planitor.utils.text import fold, slugify

MunicipalityAttributes = NamedTuple(
    "MunicipalityAttributes", name=str, osm_id=int, placenames=Tuple[str]
)

MUNICIPALITIES = {
    # These are `name`, `osm_id` tuples
    "reykjavik": MunicipalityAttributes("Reykjavík", "2580605", None),
    "hafnarfjordur": MunicipalityAttributes("Hafnarfjörður", "2582273", None),
    "arborg": MunicipalityAttributes(
        "Árborg",
        None,
        (
            "Sandvík",
            "Stokkseyri",
            "Eyrarbakki",
            "Selfoss",
        ),
    ),
}


def get_or_create_municipality(db, slug) -> Tuple[Attachment, bool]:
    name, osm_id, _ = MUNICIPALITIES[slug]
    muni = db.query(Municipality).filter_by(slug=slug).first()
    created = False
    if muni is None:
        muni = Municipality(name=name, geoname_osm_id=osm_id, slug=slug)
        db.add(muni)
        created = True
    return muni, created


def get_or_create_council(
    db, municipality, slug: str, label: str = None
) -> Tuple[Attachment, bool]:
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
            name=label or council_type.label,
        )
        db.add(council)
        created = True
    return council, created


def get_or_create_meeting(db, council, name) -> Tuple[Attachment, bool]:
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
            search_vector=func.to_tsvector(
                "simple", " ".join(yield_entity_name_search_tokens(name))
            ),
        )
        db.add(entity)
        created = True
    return entity, created


def get_or_create_case(db, serial: str, municipality: Municipality) -> Tuple[Case, bool]:
    case = db.query(Case).filter_by(serial=serial, municipality=municipality).first()
    created = False
    if case is None:
        case = Case(serial=serial, municipality=municipality)
        db.add(case)
        created = True
    return case, created


def get_or_create_case_entity(
    db: Session, case: Case, entity: Entity, applicant: bool
) -> Tuple[CaseEntity, bool]:
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


def get_or_create_attachment(db, minute, url, **items) -> Tuple[Attachment, bool]:
    attachment = (
        db.query(Attachment)
        .filter(Attachment.url == url, Attachment.minute == minute)
        .first()
    )
    created = False
    if attachment is None:
        attachment = Attachment(minute=minute, url=url, **items)
        db.add(attachment)
        created = True
    return attachment, created


def create_minute(db, meeting: Meeting, **items: dict) -> Minute:
    case_serial = items.pop("case_serial")
    case_address = items.pop("case_address")
    case_stadgreinir = items.pop("case_stadgreinir", None)

    case, case_created = get_or_create_case(db, case_serial, meeting.council.municipality)
    case.address = case_address
    case.stagreinir = case_stadgreinir

    if case_created and case_address:
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
        case.headline = minute.headline

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


def get_address(hnitnum: int) -> Optional[Address]:
    iceaddr_matches = _run_addr_query(
        "SELECT * FROM stadfong WHERE hnitnum=?;", (hnitnum,)
    )
    if not iceaddr_matches:
        return None
    return iceaddr_matches[0]


def init_address(address):
    return Address(**{k: v for k, v in address.items() if k in ADDRESS_KEYS})


def get_and_init_address(hnitnum: int) -> Optional[Address]:
    address = get_address(hnitnum)
    if address is None:
        return None
    return init_address(address)


def search_addresses(q):
    if ", " in q:
        q, placename = q.split(", ", 1)
    else:
        placename = None
    street, number, letter = get_address_lookup_params(q)
    q = Address(heiti_nf=street, husnr=number, bokst=letter or "").address
    if placename:
        q = f"{q}, {placename}"
    matches = iceaddr_suggest(q, limit=200)
    lookup_match = iceaddr_lookup(q)
    if lookup_match and lookup_match[0] not in matches:
        matches.insert(1, lookup_match[0])
    return [init_address(m) for m in matches]


def search_entities(db: Session, q: str):
    tsquery = func.websearch_to_tsquery("simple", q)
    return (
        db.query(Entity)
        .filter(Entity.search_vector.op("@@")(tsquery))
        .order_by(func.ts_rank(Entity.search_vector, tsquery))
    )


def get_or_create_address(
    db: Session,
    iceaddr_match: dict,
) -> Tuple[Address, bool]:
    address = db.query(Address).get(iceaddr_match["hnitnum"])
    created = False
    if address is None:
        address = Address(**{k: v for k, v in iceaddr_match.items() if k in ADDRESS_KEYS})
        db.add(address)
        created = True
    return address, created


def get_geoname_and_housenumber(
    db: Session, street: str, number, letter, city
) -> Tuple[Optional[Geoname], Optional[Housenumber]]:

    street_db = (
        db.query(Geoname)
        .filter_by(name=street, city=city)
        .order_by(Geoname.importance)
        .first()
    )

    if street_db is None:
        return None, None

    housenumber = (
        db.query(Housenumber)
        .filter(Housenumber.street == street_db)
        .filter(
            (Housenumber.housenumber == f"{number}{letter}")
            | (Housenumber.housenumber == str(number))
        )
        .first()
    )

    return street_db, housenumber


def update_case_address(db: Session, case: Case) -> None:
    """Update the iceaddr, geoname and housenumber attributes. There is significant
    overlaps between iceaddr and geoname functionality but good to have both.

    """

    # For municipalities like Árborg there are many placenames, but for others there is
    # only one, like Reykjavík
    placenames = MUNICIPALITIES[case.municipality.slug].placenames or [
        case.municipality.name
    ]

    street, number, letter = get_address_lookup_params(case.address)

    for placename in placenames:
        iceaddr_match = lookup_address(street, number, letter, placename)
        if iceaddr_match:
            if (
                iceaddr_match["stadur_nf"] != placename
                or iceaddr_match["svfnr"] != case.municipality.id
            ):
                continue
            address, _ = get_or_create_address(db, iceaddr_match)
            db.commit()
            case.iceaddr = address
            break

    for placename in placenames:
        geoname, housenumber = get_geoname_and_housenumber(
            db, street, number, letter, placename
        )
        case.geoname, case.housenumber = geoname, housenumber
        if geoname:
            break

    db.add(case)
    db.commit()


def update_case_status(db: Session, case: Case):
    """Query minutes in chronological meeting order, the last minute status will
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
        Entity.entity_type == EntityTypeEnum.company,
        func.lower(Entity.name) == name,
    )


MAX_LEVENSHTEIN_DISTANCE = 5


def levenshtein_company_lookup(db, name, max_distance=MAX_LEVENSHTEIN_DISTANCE):
    """As described above, we may encounter similar looking inflections of company
    names. Instead of tokenizing and lemming words (which we could ...) we just use a
    simple Levenshtein distance calculation. This will also be useful for search.

    Here we use ascii folding and rely on the slug column which is also ascii folded.
    This is also useful for quick ranking of results for typing inputs that doesn’t
    require capital letters or accented characters.

    """

    folded = clean_company_name(fold(name))
    col = func.levenshtein_less_equal(Entity.slug, folded, max_distance)
    return db.query(Entity, col).filter(col <= max_distance).order_by(col)
