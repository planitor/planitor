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
from typing import List, Generator, Optional

from reynir.bintokenizer import tokenize, PersonName
from tokenizer import TOK

from planitor import greynir
from planitor.utils.stopwords import stopwords


def get_token_meanings(token, ignore=None) -> Optional[list]:
    if ignore is None:
        ignore = []
    if token.kind not in (TOK.WORD, TOK.ENTITY, TOK.PERSON, TOK.HASHTAG):
        return None
    if token.txt in ignore:
        return None
    return token.val


def get_token_lemmas(token, ignore) -> List[str]:
    lemmas = []
    meanings = get_token_meanings(token, ignore)
    for word in meanings or []:
        if isinstance(word, PersonName):
            lemma = word.name
        else:
            lemma = word.stofn
        if lemma in stopwords:
            return []
        lemmas.append(lemma)
    return lemmas


def get_lemma_terminals(terminals, ignore) -> List[str]:
    lemmas = []
    for text, lemma, category, variants, index in terminals:
        if text in ignore:
            continue
        if category not in ("no", "so", "gata", "person"):
            continue
        if text.lower() in stopwords:
            continue
        lemmas.append(lemma)
    return lemmas


def parse_lemmas(text, ignore=None) -> Generator[str, None, None]:
    """If Greynir cannot parse we drop down to the less clever tokenizer which is inflection
    and case aware, but will give us multiple meanings for words like "svala" and "á".
    """
    if ignore is None:
        ignore = []
    for sentence in greynir.parse(text)["sentences"]:
        terminals = sentence.terminals
        if terminals is None:
            for token in tokenize(sentence.tidy_text):
                for lemma in set(get_token_lemmas(token, ignore)):
                    yield lemma
        else:
            for lemma in get_lemma_terminals(terminals, ignore):
                yield lemma


def get_wordbase(word) -> Optional[str]:
    if re.search(r"\w-\w", word) is not None:
        _, wordbase = word.rsplit("-", 1)
        return wordbase


def with_wordbases(lemmas) -> Generator[str, None, None]:
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


def get_lemmas(text, ignore=None) -> Generator[str, None, None]:
    if ignore is None:
        ignore = []
    yield from with_wordbases(parse_lemmas(text, ignore))
