from sqlalchemy.orm import Session

from .crud import (
    create_minute,
    get_or_create_case_entity,
    get_or_create_entity,
    lookup_icelandic_company_in_entities,
)
from .language.companies import extract_company_names
from .minutes import get_minute_lemmas
from .models import Meeting, Minute
from .utils.kennitala import Kennitala
from .utils.rsk import get_kennitala_from_rsk_search


def _get_entity(db: Session, name: str):
    _all = list(lookup_icelandic_company_in_entities(db, name))
    if len(_all) > 1:
        # If there is a name collision we don’t know which one to pick
        return None
    if len(_all) == 1:
        return _all[0]
    # Try doing a lookup in the RSK.is fyrirtækjaskrá
    kennitala = get_kennitala_from_rsk_search(name)
    if kennitala is not None:
        kennitala = Kennitala(kennitala)
        entity, created = get_or_create_entity(db, kennitala, name, address=None)
        if created:
            db.commit()
        return entity


def update_minute_with_entity_relations(
    db: Session, minute: Minute, entity_items: list
):
    """Here we have kennitala and name, whereas in `update_minute_with_entity_mentions`
    we only have the names. """

    case = minute.case

    # Squash duplicates
    entity_items = ({e["kennitala"]: e for e in entity_items}).values()

    # Create and add applicant companies or persons
    for items in entity_items:  # persons or companies inquiring
        kennitala = Kennitala(items.pop("kennitala"))
        if not kennitala.validate():
            continue
        entity, _ = get_or_create_entity(db, kennitala=kennitala, **items)

        case_entity, _ = get_or_create_case_entity(db, case, entity, applicant=True)
        if case_entity not in case.entities:
            case.entities.append(case_entity)

    db.commit()


def update_minute_with_entity_mentions(db: Session, minute: Minute):

    assert not db.new

    mentions = extract_company_names(minute.inquiry)

    if not mentions:
        minute.assign_entity_mentions({})
        db.add(minute)
        db.commit()
        return

    # We only want to persist mentions that have matching local entities, this is to
    # track those
    _matched_mentions = {}

    for co_name, locations in mentions.items():
        entity = _get_entity(db, co_name)
        if entity is None:
            continue
        case_entity, created = get_or_create_case_entity(
            db, minute.case, entity, applicant=False
        )
        if created:
            db.commit()
        _matched_mentions[entity.kennitala] = locations

    minute.assign_entity_mentions(_matched_mentions)
    db.add(minute)
    db.commit()


def update_minute_with_lemmas(db: Session, minute: Minute):
    minute.lemmas = get_minute_lemmas(minute)
    db.add(minute)
    db.commit()


def process_minute(db: Session, items, meeting: Meeting):

    minute = create_minute(db, meeting, **items)
    db.commit()
    case = minute.case

    # Update minute with the entities of record
    update_minute_with_entity_relations(
        db, minute, entity_items=items.pop("entities", [])
    )

    # Also associate companies mentioned in the inquiry, such as architects
    update_minute_with_entity_mentions(db, minute)

    # Populate the lemma column with lemmas from Greynir and/or tokenizer
    update_minute_with_lemmas(db, minute)

    db.add(case)
    db.commit()
