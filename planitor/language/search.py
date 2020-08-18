""" Indexing is a very processing intensive task and should be done in a background
queue worker.

This is how we index at Planitor.

1.  Lemmatize using Greynir (ex. leiguíbúðir → leiguíbúð), or if that fails,
    bintokenizer which yields all possible meanings of a word.
2.  Remove stopwords and leave only nouns, verbs, streets and persons. Postgres has
    no default stopword dictionary for Icelandic so we need to do this in Python.
3.  Persist in a column which has a ts_vector gin index on it.

This module helps find lemmas suitable for fulltext indexing.

"""

import re
from typing import List, Iterable, Optional, Set

from reynir.bintokenizer import PersonName
from reynir.bindb import BIN_Meaning
from tokenizer import TOK

from planitor import greynir
from planitor.utils.stopwords import stopwords

from .companies import extract_company_names


INDEXABLE_TOKEN_TYPES = frozenset(
    (
        TOK.ENTITY,
        TOK.HASHTAG,
        TOK.NUMBER,
        TOK.NUMWLETTER,
        TOK.ORDINAL,
        TOK.PERSON,
        TOK.SERIALNUMBER,
        TOK.WORD,
        TOK.YEAR,
        TOK.DATEREL,
        TOK.DATEABS,
        TOK.MOLECULE,
        TOK.COMPANY,
        TOK.MEASUREMENT,
    )
)


def get_token_lemmas(token, ignore) -> List[str]:
    if ignore is None:
        ignore = []
    if token.kind not in INDEXABLE_TOKEN_TYPES or token.txt in ignore:
        return []
    if token.kind == TOK.NUMWLETTER:
        # For tokens like "12a" return both "12a" and "12"
        num, letter = token.val
        return [f"{num}{letter}", str(num)]
    if token.kind not in (TOK.PERSON, TOK.WORD, TOK.ENTITY) or token.val is None:
        return [token.txt]
    lemmas = []
    for word in token.val:
        if isinstance(word, PersonName):
            lemma = word.name
        else:
            lemma = word.stofn
        if lemma in stopwords:
            return []
        if lemma not in lemmas:
            lemmas.append(lemma)
    return lemmas


def get_lemma_terminals(terminals, ignore=None) -> List[str]:
    if ignore is None:
        ignore = []
    lemmas = []
    for text, lemma, category, variants, index in terminals:
        if text in ignore:
            continue
        if category not in (
            "no",
            "so",
            "gata",
            "person",
            "talameðbókstaf",
            "tala",
            "fyrirtæki",
            "mælieining",
            "dagsafs",
            "dagsföst",
            "sameind",  # case serials are marked as sameind sometimes
        ):
            continue
        if text.lower() in stopwords:
            continue
        lemmas.append(lemma)
    return lemmas


def parse_lemmas(text: str, ignore=None, max_sent_tokens=40) -> Iterable[str]:
    """If Greynir cannot parse we drop down to the less clever tokenizer which is inflection
    and case aware, but will give us multiple meanings for words like "svala" and "á".
    ReynirPackage has an extremely high `max_sent_tokens` default at 90. This can easily
    max out memory of a worker process so we set it much lower.
    """
    if ignore is None:
        ignore = []
    job = greynir.parse(text, max_sent_tokens=max_sent_tokens)
    for sentence in job["sentences"]:
        terminals = sentence.terminals
        if terminals is None:
            for token in sentence.tokens:
                for lemma in get_token_lemmas(token, ignore):
                    yield lemma
        else:
            for lemma in get_lemma_terminals(terminals, ignore):
                yield lemma
    for lemma in extract_company_names(text, sentences=job["sentences"]).keys():
        yield lemma


def get_wordbase(word) -> Optional[str]:
    if re.search(r"\w-\w", word) is not None:
        _, wordbase = word.rsplit("-", 1)
        return wordbase


def with_wordbases(lemmas) -> Iterable[str]:
    """ If word is a compound word, Greynir adds a dash. In this case, yield the base of
    the word like "skemmdir" in "raka-skemmdir", along with the compound word without
    the dash.
    """
    for lemma in lemmas:
        wordbase = get_wordbase(lemma)
        if wordbase is not None:
            yield wordbase
            yield lemma.replace("-", "")
        else:
            yield lemma


def get_lemmas(text, ignore=None) -> Iterable[str]:
    if ignore is None:
        ignore = []
    yield from with_wordbases(parse_lemmas(text, ignore))


def get_wordforms(bindb, term) -> Set[str]:
    matches = {term}

    _, meanings = bindb.lookup_word(term, auto_uppercase=True)
    for meaning in meanings:
        print(
            _,
            {
                "stofn": meaning.stofn,
                "utg": meaning.utg,
                "ordfl": meaning.ordfl,
                "fl": meaning.fl,
                "ordmynd": meaning.ordmynd,
                "beyging": meaning.beyging,
            },
        )

        def _filter(beyging) -> bool:
            return True

        results = map(
            BIN_Meaning._make,
            bindb._compressed_bin.lookup(meaning.stofn, beyging_func=_filter),
        )
        matches.update(tuple(m.ordmynd.lower() for m in results or []))

        """
        cases = [s.encode("latin-1") for s in ("NF", "ÞF", "ÞGF", "EF")]
        for singular in (True, False):
            for indefinite in (True, False):
                for case in cases:
                    options = dict(case=case, singular=singular, indefinite=indefinite)
                    def _filter(beyging) -> bool:
                        if case not in
                    results = map(
                        BIN_Meaning._make,
                        bindb._compressed_bin.lookup(meaning.stofn, **options),
                    )
                    matches.update(tuple(m.ordmynd.lower() for m in results or []))
        """

    return matches


def lemmatize_query(search_query) -> str:
    """ We need to alter the query to get around a few limitations of the Postgres simple
    dictionary and the way things are indexed. Read the inline comments for a step by
    step explanation.

    """

    # Only title case if this is an "exact" web query with quotes
    if (search_query[0], search_query[-1]) == ('"', '"'):
        terms = search_query.strip('"').split()
        return '"{}"'.format(" ".join(term.title() for term in terms))

    def repl(matchobj):
        query = matchobj.group(0).title()
        # Use titleize the term because the Postgres simple dictionary doesn’t lowercase
        # accented characters and the lemma column preserves case
        lemmas = parse_lemmas(query)

        # Take the first matched lemma, if there are lemmas, and remove dashes from
        # compound words
        lemmas = [lemma.replace("-", "").title() for lemma in lemmas][:1]

        # Ensure the search term is included as is, because sometimes we interpret
        # things like "Árni" as a verb
        lemmas = {query, *lemmas}

        if len(lemmas) == 1:
            # Return the
            return lemmas.pop()

        return " or ".join(sorted(lemmas))

    return re.sub(r"\w+", repl, search_query)
