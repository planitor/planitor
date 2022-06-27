import re
from typing import Iterable, List

from dramatiq import group, pipeline
from sentry_sdk import capture_exception
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import dramatiq, greynir
from .attachments import update_pdf_attachment
from .crud import (
    create_minute,
    get_or_create_attachment,
    get_or_create_case_entity,
    get_or_create_entity,
    lookup_icelandic_company_in_entities,
)
from .database import db_context
from .language.companies import extract_company_names
from .minutes import get_minute_lemmas
from .models import Meeting, Minute, Response
from .monitor import create_deliveries, send_meeting_emails
from .notifications import send_applicant_notifications
from .utils.kennitala import Kennitala


def _get_entity(db: Session, name: str):
    _all = list(lookup_icelandic_company_in_entities(db, name))
    if len(_all) > 1:
        # If there is a name collision we don’t know which one to pick
        return None
    if len(_all) == 1:
        return _all[0]
    # Try doing a lookup in the RSK.is fyrirtækjaskrá
    # RSK now applies a ReCAPTCHA so we will try again later:

    """
    kennitala = get_kennitala_from_rsk_search(name)
    if kennitala is not None:
        kennitala = Kennitala(kennitala)
        entity, created = get_or_create_entity(db, kennitala, name, address=None)
        if created:
            db.commit()
        return entity
    """


def update_minute_with_entity_relations(
    db: Session, minute: Minute, entity_items: list
):
    """Here we have kennitala and name, whereas in `update_minute_with_entity_mentions`
    we only have the names."""

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


def _update_minute_with_entity_mentions(db, minute):

    if minute.inquiry is None:
        return

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


@dramatiq.actor
def update_minute_with_entity_mentions(minute_id: int):

    with db_context() as db:

        minute = db.query(Minute).get(minute_id)
        _update_minute_with_entity_mentions(db, minute)


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
            noun = str(noun)
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
        response = Response(
            order=i, headline=headline, contents=contents, minute=minute
        )
        response.subjects = get_subjects(response.headline)
        db.add(response)
        db.commit()


def _update_minute_search_vector(minute: Minute, db: Session):
    lemmas = get_minute_lemmas(minute)
    print("MINUTE", minute.id, lemmas)
    minute.search_vector = func.to_tsvector("simple", " ".join(lemmas))
    minute.lemmas = ", ".join(lemmas)
    db.add(minute)


@dramatiq.actor
def update_minute_search_vector(minute_id: int, force: bool = False):
    with db_context() as db:
        minute = db.query(Minute).get(minute_id)
        if minute is None:
            return
        if not minute.search_vector or force:
            try:
                _update_minute_search_vector(minute, db)
            except Exception as e:
                capture_exception(e)
            db.commit()


def update_minute_with_attachments(
    db: Session, minute: Minute, attachments_items: List[dict]
):
    for items in attachments_items:
        attachment, _ = get_or_create_attachment(db, minute, **items)
        db.commit()
        update_pdf_attachment.send(attachment.id)


def process_minute(db: Session, item: dict, meeting: Meeting):

    entity_items = item.pop("entities", [])
    response_items = item.pop("responses", [])
    attachment_items = item.pop("attachments", [])

    minute = create_minute(db, meeting, **item)
    db.commit()
    case = minute.case

    # Update minute with the entities of record
    update_minute_with_entity_relations(db, minute, entity_items)

    # Update minute with the responses
    update_minute_with_response_items(db, minute, response_items)

    # Add attachment
    update_minute_with_attachments(db, minute, attachment_items)

    assert minute.id

    # Return messages that can be pipelined and processed before we send notification
    messages = [
        # Also associate companies mentioned in the inquiry, such as architects
        update_minute_with_entity_mentions.message_with_options(
            args=(minute.id,), pipe_ignore=True
        ),
        # Populate the lemma column with lemmas from Greynir and/or tokenizer
        update_minute_search_vector.message_with_options(
            args=(minute.id,), pipe_ignore=True
        ),
        # ... run matches
        create_deliveries.message_with_options(args=(minute.id,), pipe_ignore=True),
        send_applicant_notifications.message_with_options(
            args=(minute.id,), pipe_ignore=True
        ),
    ]

    db.add(case)
    db.commit()

    return messages


def process_minutes(db: Session, items: Iterable[dict], meeting: Meeting) -> None:

    pipes = []

    for data in items:
        if data is not None:
            messages = process_minute(db, data, meeting)
            pipe = pipeline(messages)
            pipes.append(pipe)

    if not pipes:
        return

    g = group(pipes)
    g.add_completion_callback(send_meeting_emails.message())
    g.run()
