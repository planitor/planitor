import re
import math
from typing import Set, Generator

from jinja2 import Markup
from reynir.bindb import BIN_Db
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, contains_eager
from iceaddr import iceaddr_suggest

from planitor.language.search import get_wordforms, lemmatize_query
from planitor.models import Minute, Case, Meeting, Council


def get_tsquery(search_query):
    """People frequently compose search queries with plural form, for example
    "bílakjallarar" or use non-nominative inclensions. It’s important to depluralize
    this. The `parse_lemmas` achieves this for us."""
    return func.websearch_to_tsquery("simple", lemmatize_query(search_query))


def get_terms_from_query(tsquerytree: str):
    """querytree in Postgres takes a tsquery and strips negated terms and stopwords.
    This returns the terms considered, stripped of the boolean logic tokens."""

    # split on <->, | and & characters
    quoted_terms = re.split(r" <\d+> | <-> | \| | & ", tsquerytree)

    # remove single quotes around terms
    terms = [t[1:-1] for t in quoted_terms]
    return terms


HIGHLIGHT_RANGE = 30


def iter_preview_fragments(
    document: str, highlight_terms: Set[str], max_fragments: int = 3
) -> Generator[Markup, None, None]:
    """Find segments within a document where instances of terms appear. Used to display
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

    if max_fragments:
        spans = spans[:max_fragments]

    if not spans:
        # No search terms to highlight, create three zero-length highlights so that the
        # start of the document is included as a preview
        spans = [
            (HIGHLIGHT_RANGE, HIGHLIGHT_RANGE),
        ]

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
            before = Markup(f"…{before.lstrip()}")

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
            after = Markup(f"{after.rstrip()}…")

        yield (before + Markup(f"<strong>{document[start:end]}</strong>") + after).strip()


class Pagination:

    PER_PAGE = 15
    NAV_SEGMENT_SIZE = 6

    def __init__(self, query, count_query, number: int):
        self.count = count_query.scalar()
        self.number = number if number > 0 else 1
        self.total_pages = int(math.ceil(self.count / self.PER_PAGE))
        self.pages = list(range(1, self.total_pages + 1))  # 1-based indexing of all pages
        self.query = query.offset(self.PER_PAGE * (number - 1)).limit(self.PER_PAGE)

    def get_page_segments(self):
        """Always show first three pages and last three pages.
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
    """Queries are human formed strings. Before we hand off to Postgres
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
        self.query, count = self.get_query_and_count()
        self.page = Pagination(self.query, count, page or 0)

    def get_query_and_count(self):
        tsquery = get_tsquery(self.search_query)

        # Only take first three suggestions
        hnitnums = [
            address["hnitnum"] for address in iceaddr_suggest(self.search_query)[:3]
        ]

        filter_ = Minute.search_vector.op("@@")(tsquery)
        if hnitnums:
            filter_ = or_(filter_, Case.address_id.in_(hnitnums))
        order_bys = [Meeting.start.desc()]
        if hnitnums:
            # order_bys.insert(0, Case.address_id.in_(hnitnums))
            pass

        return (
            (
                self.db.query(Minute)
                .join(Minute.case)
                .join(Minute.meeting)
                .join(Meeting.council)
                .join(Council.municipality)
                .options(
                    contains_eager(Minute.meeting)
                    .contains_eager(Meeting.council)
                    .contains_eager(Council.municipality),
                    contains_eager(Minute.case),
                )
                .filter(filter_)
                .order_by(
                    *order_bys
                )  # Relavance ranking is `func.ts_rank(tsvector, tsquery)`
            ),
            (self.db.query(func.count(Minute.id)).join(Case).filter(filter_)),
        )

    def get_highlight_terms(self) -> Set[str]:
        """Return the query and ask Postgres what terms were indexed in the query,
        which will be used for highlighting. We ask the Postgres querytree because it
        cleans up a lot of things, removes negated terms, lowercases and more."""

        index_terms = get_terms_from_query(
            self.db.query(func.querytree(get_tsquery(self.search_query))).scalar()
        )
        highlight_terms = set()
        with BIN_Db.get_db() as bindb:
            for term in index_terms:
                highlight_terms.update(get_wordforms(bindb, term))
        return highlight_terms

    def get_document(self, minute: Minute) -> str:
        parts = [minute.inquiry, minute.remarks]
        # parts += [ec.entity.name for ec in (minute.case.entities or [])]
        return "\n".join(part for part in parts if part)

    def __iter__(self):
        highlight_terms = self.get_highlight_terms()
        minutes = self.page.query.all()
        for minute in minutes:
            document = self.get_document(minute)
            previews = iter_preview_fragments(document, highlight_terms)
            yield minute, previews
