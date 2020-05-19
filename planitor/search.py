import re
import math
from typing import Set

from jinja2 import Markup
from reynir.bindb import BIN_Db
from sqlalchemy import func
from sqlalchemy.orm import Session

from planitor.language.search import get_wordforms, parse_lemmas
from planitor.models import Minute


def get_terms_from_query(tsquerytree: str):
    """ querytree in Postgres takes a tsquery and strips negated terms and stopwords.
    This returns the terms considered, stripped of the boolean logic tokens. """

    # split on <->, | and & characters
    quoted_terms = re.split(r" <-> | \| | & ", tsquerytree)

    # remove single quotes around terms
    terms = [t[1:-1] for t in quoted_terms]
    return terms


HIGHLIGHT_RANGE = 30


def iter_preview_fragments(document: str, highlight_terms: Set[str]) -> Markup:
    """ Find segments within a document where instances of terms appear. Used to display
    segments of meeting minutes in search results (like google does where matched search
    terms) are bolded. Uses Jinja Markup and adds the <em> tag around matched terms.
    Also add ellipses.
    """

    spans = []

    for match in re.finditer(r"\w+", document):
        term = match.group()
        if term.lower() not in highlight_terms:
            continue

        start, end = match.span()

        # Make sure to expand the span if we have consecutively highlighted terms,
        # otherwise we will yield multiple previews for each term
        for span in spans:
            prev_start, prev_end = span

            # See if highlight segments overlap
            if prev_end + HIGHLIGHT_RANGE >= start:
                # If so, lengthen the span to include this term
                span.pop(1)
                span.append(end)
                break
        else:
            spans.append([start, end])

    for start, end in spans:

        pstart = max(0, start - HIGHLIGHT_RANGE)  # Don’t rewind past start
        pend = min(len(document), end + HIGHLIGHT_RANGE)  # Don’t forward past end

        while True:
            if pstart == 0:
                break
            if document[pstart] == " ":
                break
            pstart -= 1
            if start - pstart > (HIGHLIGHT_RANGE + 20):
                pstart = start
                break

        before = Markup.escape(document[pstart:start])
        # Add ellipses if the cursor hasn’t moved to the start of the document.
        if pstart != 0:
            before = f"…{before.lstrip()}"

        while True:
            if pend == len(document):
                break
            if document[pend] == " ":
                break
            pend += 1
            if pend - end > (HIGHLIGHT_RANGE + 20):
                pend = end
                break

        after = Markup.escape(document[end:pend])
        # Add ellipses if the cursor hasn’t moved to the end of the document.
        if pend != len(document):
            after = f"{after.rstrip()}…"

        yield (before + Markup(f"<strong>{document[start:end]}</strong>") + after).strip()


class Pagination:

    PER_PAGE = 15
    NAV_SEGMENT_SIZE = 6

    def __init__(self, query, number: int):
        self.count = query.count()
        self.number = number if number > 0 else 1
        self.total_pages = int(math.ceil(self.count / self.PER_PAGE))
        self.pages = list(range(1, self.total_pages + 1))  # 1-based indexing of all pages
        self.query = query.offset(self.PER_PAGE * (number - 1)).limit(self.PER_PAGE)

    def get_page_segments(self):
        """ Always show first three pages and last three pages.
        This is to render something like this: 1, 2, 3 ... 65 _66_ 67 ... 111, 112, 113
        """
        head = self.pages[0 : min(self.NAV_SEGMENT_SIZE, len(self.pages))]
        tail = self.pages[-(min(self.NAV_SEGMENT_SIZE + 1, len(self.pages))) : -1]
        range_page = self.pages[
            max(0, self.number - self.NAV_SEGMENT_SIZE) : min(
                len(self.pages), self.number + self.NAV_SEGMENT_SIZE + 1
            )
        ]
        head = [p for p in head if p not in range_page]
        tail = [p for p in tail if p not in range_page]
        return head, range_page, tail

    @property
    def has_next(self):
        if self.count == 0:
            return False
        return self.number != self.pages[-1]


class MinuteResults:
    """ Queries are human formed strings. Before we hand off to Postgres
    websearch_to_tsquery we lemmatize each word as people frequently search for things
    like "Brautarholti" og "bílakjallarar" which is not the nominative inflection and
    not singular. In the index we lemmatize so let’s try to use lemmas when searching.
    However when results are displayed people like to see highlighted segments where
    the search terms appear.

    Pagination is handled by this class.

    This class handles pagination and rendering HTML previews with the search terms
    highlighted.
    """

    def __init__(self, db: Session, search_query: str, page: int):
        self.db = db
        self.search_query = search_query

        query = self.get_query()
        self.page = Pagination(query, page or 0)

    def get_tsquery(self):
        """ People frequently compose search queries with plural form, for example
        "bílakjallarar" or use non-nominative inclensions. It’s important to depluralize
        this. The `parse_lemmas` achieves this for us. """

        def repl(matchobj):
            lemmas = list(parse_lemmas(matchobj.group(0).title()))
            return lemmas[0].replace("-", "") if lemmas else matchobj.group(0)

        search_query = re.sub(r"\w+", repl, self.search_query)
        return func.websearch_to_tsquery("simple", search_query)

    def get_query(self):
        tsvector = func.to_tsvector("simple", Minute.lemmas)
        tsquery = self.get_tsquery()
        return (
            self.db.query(Minute)
            .filter(tsvector.op("@@")(tsquery))
            .order_by(func.ts_rank(tsvector, tsquery))
        )

    def get_highlight_terms(self) -> Set[str]:
        """ Return the query and ask Postgres what terms were indexed in the query,
        which will be used for highlighting. We ask the Postgres querytree because it
        cleans up a lot of things, removes negated terms, lowercases and more. """

        index_terms = get_terms_from_query(
            self.db.query(func.querytree(self.get_tsquery())).scalar()
        )
        highlight_terms = set()
        with BIN_Db.get_db() as bindb:
            for term in index_terms:
                highlight_terms.update(get_wordforms(bindb, term))
        return highlight_terms

    def get_document(self, minute: Minute) -> str:
        return " \n".join(
            part for part in (minute.headline, minute.inquiry, minute.remarks) if part
        )

    def __iter__(self):
        highlight_terms = self.get_highlight_terms()
        for minute in self.page.query.all():
            document = self.get_document(minute)
            previews = iter_preview_fragments(document, highlight_terms)
            yield minute, previews
