""" Indexing is a very processing intensive task and should be done in a background
queue worker.

This is how we index at Planitor.

1.  Lemmatize using the lemma.solberg.is API (based on BÍN data).
2.  Remove stopwords. Postgres has no default stopword dictionary for Icelandic
    so we need to do this in Python.
3.  Persist in a column which has a ts_vector gin index on it.

This module helps find lemmas suitable for fulltext indexing.

Previously this used Greynir which required loading large language models into memory.
Now we use a lightweight HTTP API which significantly reduces worker memory usage.
"""

import re
from typing import Iterable, List, Optional, Set

from reynir.bindb import GreynirBin

from planitor.utils.stopwords import stopwords

from .lemma_api import lemmatize_text, lemmatize_word


def get_wordbase(word) -> Optional[str]:
    """If word is a compound word with a dash, return the base (right part)."""
    if re.search(r"\w-\w", word) is not None:
        _, wordbase = word.rsplit("-", 1)
        return wordbase
    return None


def with_wordbases(lemmas: Iterable[str]) -> Iterable[str]:
    """If word is a compound word, yield the base of the word like "skemmdir" in
    "raka-skemmdir", along with the compound word without the dash.
    """
    for lemma in lemmas:
        wordbase = get_wordbase(lemma)
        if wordbase is not None:
            yield wordbase
            yield lemma.replace("-", "")
        else:
            yield lemma


def filter_stopwords(lemmas: Iterable[str]) -> Iterable[str]:
    """Filter out stopwords from lemmas."""
    for lemma in lemmas:
        if lemma.lower() not in stopwords:
            yield lemma


def get_lemmas(text: str, ignore: List[str] = None) -> Iterable[str]:
    """
    Get lemmas from text suitable for search indexing.
    
    Uses the lemma.solberg.is API for lemmatization, then filters stopwords.
    
    Args:
        text: The text to lemmatize
        ignore: List of terms to ignore (currently not used with API)
    
    Yields:
        Lemmas suitable for indexing
    """
    if ignore is None:
        ignore = []
    
    # Get lemmas from the API
    lemmas = lemmatize_text(text)
    
    # Filter out ignored terms and stopwords
    filtered = (l for l in lemmas if l not in ignore)
    filtered = filter_stopwords(filtered)
    
    # Handle compound words
    yield from with_wordbases(filtered)


def get_wordforms(bindb: GreynirBin, term: str) -> Set[str]:
    """
    Get all word forms for a term (for search result highlighting).
    
    This expands a lemma to all its inflected forms so we can highlight
    any form in search results.
    
    Note: This still uses GreynirBin as it's a read-time operation for
    search highlighting, not a write-time indexing operation.
    """
    matches = {term}

    _, meanings = bindb.lookup_g(term, auto_uppercase=True)
    for meaning in meanings:
        for f in (
            bindb.lookup_nominative,
            bindb.lookup_accusative,
            bindb.lookup_dative,
            bindb.lookup_genitive,
        ):
            matches.update(tuple(m.ord.lower() for m in (f(meaning.stofn) or [])))

    return matches


def lemmatize_query(search_query: str) -> str:
    """
    Transform a search query by lemmatizing each term.
    
    This helps match queries like "bílakjallarar" (plural) to indexed lemmas
    like "bílakjallari" (singular nominative).
    
    For exact phrase queries (in quotes), preserves the phrase but titlecases terms.
    """
    # Handle exact phrase queries with quotes
    if len(search_query) >= 2 and (search_query[0], search_query[-1]) == ('"', '"'):
        terms = search_query.strip('"').split()
        return '"{}"'.format(" ".join(term.title() for term in terms))

    def repl(matchobj):
        query = matchobj.group(0)
        query_title = query.title()
        
        # Get lemmas for this term
        lemmas = lemmatize_word(query)
        
        # Remove dashes from compound words and titlecase
        lemmas = [lemma.replace("-", "").title() for lemma in lemmas][:1]
        
        # Include original term as fallback (handles cases like "Árni" interpreted as verb)
        lemmas = {query_title, *lemmas}
        
        if len(lemmas) == 1:
            return lemmas.pop()
        
        return " or ".join(sorted(lemmas))

    return re.sub(r"\w+", repl, search_query)


# Legacy function stubs for backwards compatibility with tests
# These are no longer used in production but kept for test compatibility

def parse_lemmas(text: str, ignore=None, max_sent_tokens=40) -> Iterable[str]:
    """Legacy wrapper - now uses lemma API instead of Greynir."""
    if ignore is None:
        ignore = []
    lemmas = lemmatize_text(text)
    for lemma in lemmas:
        if lemma not in ignore:
            yield lemma


def get_token_lemmas(token, ignore=None) -> List[str]:
    """Legacy stub - tokens are now handled by the API."""
    if ignore is None:
        ignore = []
    # The API handles tokenization internally, so this is just a passthrough
    # for any code that still calls it directly
    if hasattr(token, 'txt'):
        lemmas = lemmatize_word(token.txt)
        return [l for l in lemmas if l not in ignore]
    return []
