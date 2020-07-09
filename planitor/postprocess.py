import re
from typing import List
from sqlalchemy.orm import Session

from . import dramatiq, greynir
from .attachments import update_pdf_attachment
from .crud import (
    create_minute,
    get_or_create_case_entity,
    get_or_create_entity,
    get_or_create_attachment,
    lookup_icelandic_company_in_entities,
)
from .database import db_context
from .language.companies import extract_company_names
from .minutes import get_minute_lemmas
from .models import Meeting, Minute, Response
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


def update_minute_with_entity_relations(db: Session, minute: Minute, entity_items: list):
    """Here we have kennitala and name, whereas in `update_minute_with_entity_mentions`
    we only have the names. """

    case = minute.case

    # Squash duplicates
    _entity_items = {e["kennitala"]: e for e in entity_items}

    # Create and add applicant companies or persons
    for items in _entity_items.values():  # persons or companies inquiring
        kennitala = Kennitala(items.pop("kennitala"))
        if not kennitala.validate():
            continue
        entity, _ = get_or_create_entity(db, kennitala=kennitala, **items)

        case_entity, _ = get_or_create_case_entity(db, case, entity, applicant=True)
        if case_entity not in case.entities:
            case.entities.append(case_entity)

    db.commit()


@dramatiq.actor
def update_minute_with_entity_mentions(minute_id: int):

    with db_context() as db:

        minute = db.query(Minute).get(minute_id)

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


headline_pattern = re.compile(
    r"(?:Áheyrnarfulltrúi|Fulltrúar) (.+) (?:leggur|leggja) fram svohljóðandi bókun:"
)


def get_subjects(headline):
    subjects = []
    corrections = {
        "Pírati": "Píratar",
        "fólk": "Flokkur fólksins",
        "flokkur": None,
    }
    match = re.match(headline_pattern, headline)
    if match is not None:
        sentence = greynir.parse_single(headline)
        if not sentence.score:
            return subjects
        try:
            nouns = sentence.tree.S.IP.NP_SUBJ.NP_POSS.nouns
        except AttributeError:
            return subjects
        for noun in nouns:
            if noun in corrections:
                noun = corrections[noun]
                if noun is None:
                    continue
            else:
                noun = noun.title()
            subjects.append(noun)
    return subjects


def update_minute_with_response_items(
    db: Session, minute: Minute, response_items: List[List[str]]
) -> None:
    for i, (headline, contents) in enumerate(response_items):
        response = Response(order=i, headline=headline, contents=contents, minute=minute)
        response.subjects = get_subjects(response.headline)
        db.add(response)
        db.commit()


@dramatiq.actor
def update_minute_with_lemmas(minute_id: int, force: bool = False, db: Session = None):
    def inner(db):
        minute = db.query(Minute).get(minute_id)
        if not minute.lemmas or force:
            lemmas = get_minute_lemmas(minute)
            minute.lemmas = ", ".join(lemmas)
            assert isinstance(minute.lemmas, str)
            db.add(minute)
            db.commit()
            return lemmas

    if db is not None:
        lemmas = inner(db)
    else:
        with db_context() as db:
            lemmas = inner(db)
    return lemmas


def update_minute_with_attachments(db, minute, attachments_items):
    for items in attachments_items:
        attachment = get_or_create_attachment(db, minute, **items)
        update_pdf_attachment.send(attachment.id)
        db.commit()


def process_minute(db: Session, items: dict, meeting: Meeting):

    entity_items = items.pop("entities", [])
    response_items = items.pop("responses", [])
    attachment_items = items.pop("attachments", [])

    minute = create_minute(db, meeting, **items)
    db.commit()
    case = minute.case

    # Update minute with the entities of record
    update_minute_with_entity_relations(db, minute, entity_items)

    # Update minute with the responses
    update_minute_with_response_items(db, minute, response_items)

    # Also associate companies mentioned in the inquiry, such as architects
    update_minute_with_entity_mentions.send(minute.id)

    # Populate the lemma column with lemmas from Greynir and/or tokenizer
    update_minute_with_lemmas.send(minute.id)

    # Add attachment
    update_minute_with_attachments(db, minute, attachment_items)

    db.add(case)
    db.commit()
