import re
from typing import Iterable, List

from dramatiq import group, pipeline
from sentry_sdk import capture_exception
from sqlalchemy import func, text
from sqlalchemy.orm import Session, defer

from . import dramatiq, greynir
from .attachments import update_pdf_attachment
from .crud import (
    create_minute,
    get_or_create_attachment,
    get_or_create_case_entity,
    get_or_create_entity,
    lookup_company_in_contacts,
    lookup_icelandic_company_in_entities,
    lookup_person_in_contacts,
)
from .database import db_context
from .language.companies import extract_company_names
from .language.persons import extract_person_names
from .minutes import get_minute_lemmas
from .models import Meeting, Minute, Response
from .monitor import create_deliveries, send_meeting_emails
from .notifications import send_applicant_notifications
from .utils.kennitala import Kennitala

# Matches "DDMMYY-NNNN " at the start of a company name regex match
_KT_PREFIX_RE = re.compile(r"^(\d{6})-?(\d{4})\s+")


def _split_kt_prefix(name):
    """If name starts with a kennitala (e.g. '590269-1749 Skeljungur hf.'),
    return (kennitala_digits, company_name). Otherwise return (None, name)."""
    m = _KT_PREFIX_RE.match(name)
    if m:
        return m.group(1) + m.group(2), name[m.end():]
    return None, name


def _get_entity(db: Session, name: str):
    _all = list(lookup_icelandic_company_in_entities(db, name))
    if len(_all) > 1:
        # If there is a name collision we don’t know which one to pick
        return None
    if len(_all) == 1:
        return _all[0]
    # Fallback: check company_contacts lookup table (populated from skatturinn.is)
    contact = lookup_company_in_contacts(db, name)
    if contact is not None:
        kennitala = Kennitala(contact.kennitala)
        if kennitala.validate():
            entity, created = get_or_create_entity(
                db, kennitala, name, address=None
            )
            if created:
                db.commit()
            return entity
    return None


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


def _update_entity_mentions_raw(db, minute_id: int, mentions: dict):
    """Update entity_mentions using raw SQL to avoid SQLAlchemy-Utils composite type bug."""
    if not mentions:
        # Set to empty array
        db.execute(
            text("UPDATE minutes SET entity_mentions = '{}' WHERE id = :id"),
            {"id": minute_id}
        )
    else:
        # Build array of ROW values
        rows = []
        for kennitala, locations in mentions.items():
            for start, end in locations:
                rows.append(f"ROW('{kennitala}', {start}, {end})::entity_mention_type")
        array_literal = "ARRAY[" + ", ".join(rows) + "]"
        db.execute(
            text(f"UPDATE minutes SET entity_mentions = {array_literal} WHERE id = :id"),
            {"id": minute_id}
        )
    db.commit()


def _update_minute_with_entity_mentions(db, minute):

    if minute.inquiry is None:
        return

    # Parse text once with Greynir, share sentences between extractors
    sentences = greynir.parse(minute.inquiry)["sentences"]

    company_mentions = extract_company_names(minute.inquiry, sentences=sentences)
    person_mentions = extract_person_names(minute.inquiry, sentences=sentences)

    if not company_mentions and not person_mentions:
        _update_entity_mentions_raw(db, minute.id, {})
        return

    # We only want to persist mentions that have matching local entities
    _matched_mentions = {}

    # Greynir-normalized company mentions — lookup in entities table
    for co_name, locations in company_mentions.items():
        # Check for inline kennitala prefix (e.g. "590269-1749 Skeljungur hf.")
        kt_digits, company_name = _split_kt_prefix(co_name)
        if kt_digits:
            kennitala = Kennitala(kt_digits)
            if kennitala.validate():
                entity, created = get_or_create_entity(
                    db, kennitala, company_name, address=None
                )
                if created:
                    db.commit()
                case_entity, created = get_or_create_case_entity(
                    db, minute.case, entity, applicant=False
                )
                if created:
                    db.commit()
                _matched_mentions[entity.kennitala] = locations
                continue
        entity = _get_entity(db, co_name)
        if entity is None:
            continue
        case_entity, created = get_or_create_case_entity(
            db, minute.case, entity, applicant=False
        )
        if created:
            db.commit()
        _matched_mentions[entity.kennitala] = locations

    # Person mentions — lookup in person_contacts table
    for canonical_name, locations in person_mentions.items():
        contact = lookup_person_in_contacts(db, canonical_name)
        if contact is None:
            continue
        kennitala = Kennitala(contact.kennitala)
        if not kennitala.validate():
            continue
        entity, created = get_or_create_entity(
            db, kennitala, canonical_name, address=None
        )
        if created:
            db.commit()
        case_entity, created = get_or_create_case_entity(
            db, minute.case, entity, applicant=False
        )
        if created:
            db.commit()
        if entity.kennitala in _matched_mentions:
            _matched_mentions[entity.kennitala].extend(locations)
        else:
            _matched_mentions[entity.kennitala] = locations

    _update_entity_mentions_raw(db, minute.id, _matched_mentions)


@dramatiq.actor
def update_minute_with_entity_mentions(minute_id: int):

    with db_context() as db:
        # Defer entity_mentions to avoid SQLAlchemy-Utils composite type deserialization bug
        minute = db.query(Minute).options(defer(Minute.entity_mentions)).get(minute_id)
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
    minute.search_vector = func.to_tsvector("simple", " ".join(lemmas))
    minute.lemmas = ", ".join(lemmas)
    db.add(minute)


@dramatiq.actor
def update_minute_search_vector(minute_id: int, force: bool = False):
    with db_context() as db:
        # Defer entity_mentions to avoid SQLAlchemy-Utils composite type deserialization bug
        minute = db.query(Minute).options(defer(Minute.entity_mentions)).get(minute_id)
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
        # Delivery matching (creates delivery rows but doesn't send emails)
        create_deliveries.message_with_options(args=(minute.id,), pipe_ignore=True),
        # Email sending disabled:
        # send_applicant_notifications.message_with_options(
        #     args=(minute.id,), pipe_ignore=True
        # ),
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
    # Email sending disabled:
    # g.add_completion_callback(send_meeting_emails.message())
    g.run()
