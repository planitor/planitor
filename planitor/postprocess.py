from tokenizer import TOK
from reynir.bintokenizer import _GENDER_SET

from . import greynir
from .crud import get_or_create_tag, get_or_create_case_tag
from .utils.stopwords import stopwords


INTERESTING_TOKENS = (TOK.WORD, TOK.ENTITY)


def yield_noun_stems(text):
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


def get_tag_suggestions_for_minute(minute):
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
