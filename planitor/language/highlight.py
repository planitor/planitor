import re
from reynir.bindb import BIN_Db
from reynir.bintokenizer import tokenize
from jinja2 import Markup

from .search import get_token_meanings, get_token_lemmas


def get_minute_document(minute) -> str:
    return "\n".join(part for part in (minute.inquiry, minute.remarks,) if part)


def explode_wordforms(query):

    # Create big string with both inquiry and remarks
    matches = set()

    with BIN_Db.get_db() as bindb:
        for match in re.finditer(r"\w+", query):
            query_word = match.group(0)
            _, meanings = bindb.lookup_word(query_word, auto_uppercase=True)
            for meaning in meanings:
                for f in (
                    bindb.lookup_nominative,
                    bindb.lookup_accusative,
                    bindb.lookup_dative,
                    bindb.lookup_genitive,
                ):
                    matches.update(
                        tuple(m.ordmynd.lower() for m in (f(meaning.stofn) or []))
                    )

    return matches


def match_tokens(document: str, words: list):
    for token in tokenize(document):
        if token.txt and token.txt.lower() in words:
            yield token.txt


def get_highlighted_minute_preview(minute, query):
    """ Yields Markup blocks where segment of text appears. We will expand query terms
    to all token meanings from BÍN to get a complete match set for potential highlights
    of all wordforms. """
    document = get_minute_document(minute)
    highlights = explode_wordforms(query)
    print("wordforms", highlights)
    for match in match_tokens(document, highlights):
        print(match)
        yield match
