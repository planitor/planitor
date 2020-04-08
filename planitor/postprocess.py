from tokenizer import TOK
from reynir.bintokenizer import _GENDER_SET
from sqlalchemy.orm import Session

from . import greynir
from .models import Minute
from .crud import (
    get_or_create_tag,
    get_or_create_case_tag,
    get_or_create_entity,
    get_or_create_case_entity,
    lookup_icelandic_company_in_entities,
)
from .language import extract_company_names
from .utils.stopwords import stopwords
from .utils.rsk import get_kennitala_from_rsk_search
from .utils.kennitala import Kennitala


INTERESTING_TOKENS = (TOK.WORD, TOK.ENTITY)


def yield_noun_stems(text: str):
    for token in greynir.tokenize(text):

        if token.kind not in INTERESTING_TOKENS or not token.val:
            continue

        # Skip non-nouns
        for meaning in token.val:
            if meaning.ordfl in _GENDER_SET:
                if meaning.stofn.lower() not in stopwords:
                    break
        else:
            continue

        yield meaning.stofn


def get_tag_suggestions_for_minute(minute: Minute):
    tags = set()
    text = "\n".join((minute.inquiry, minute.remarks, minute.headline))
    for tag in yield_noun_stems(text):
        tags.add(tag)
    return tags


def tag_minute(db, minute):
    case = minute.case
    for tag in get_tag_suggestions_for_minute(minute):
        tag, _ = get_or_create_tag(db, tag)
        case_tag, _ = get_or_create_case_tag(db, tag, case)
        case_tag.minute = minute
        if case_tag not in case.tags:
            case.tags.append(case_tag)


def _get_entity(db: Session, name: str):
    _all = list(lookup_icelandic_company_in_entities(db, name))
    if len(_all) > 1:
        # If there is a name collision we don’t know which one to pick
        return None
    if len(_all) == 1:
        return _all[0]
    kennitala = get_kennitala_from_rsk_search(name)
    if kennitala is not None:
        kennitala = Kennitala(kennitala)
        entity, created = get_or_create_entity(db, kennitala, name, address=None)
        if created:
            db.commit()
        return entity


def update_minute_with_entity_mentions(db: Session, minute: Minute):

    assert not db.new

    mentions = extract_company_names(minute.inquiry)

    # We only want to persist mentions that have matching local entities, this is to
    # track those
    _matched_mentions = {}

    if not mentions:
        minute.assign_entity_mentions({})
        db.add(minute)
        db.commit()
        return

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
