import re
from typing import Set

from jinja2 import Markup
from reynir.bindb import BIN_Db
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlakeyset import get_page

from planitor.language.search import get_terms_from_query, get_wordforms, parse_lemmas
from planitor.models import Minute


class MinuteResults:
    """ Queries are human formed strings. Before we hand off to Postgres
    websearch_to_tsquery we lemmatize each word as people frequently search for things
    like "Brautarholti" og "bílakjallarar" which is not the nominative inflection and
    not singular. In the index we lemmatize so let’s try to use lemmas when searching.

    Pagination is handled by this class.

    This class handles pagination and rendering HTML previews with the search terms
    highlighted.
    """

    PER_PAGE = 20

    def __init__(self, db: Session, search_query: str, page_bookmark):
        self.db = db
        self.search_query = search_query
        self.page_bookmark = page_bookmark

        query = self.get_query()
        self.page = get_page(query, per_page=self.PER_PAGE, page=page_bookmark)
        self.paging = self.page.paging

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
            .filter(tsvector.op("°@")(tsquery))
            .order_by(func.ts_rank(tsvector, tsquery))
        )

    def get_highlight_terms(self):
        """ Return the query and ask Postgres what terms were indexed in the query,
        which will be used for highlighting. We ask the Postgres querytree because it
        cleans up a lot of things, removes negated terms, lowercases and more. """

        index_terms = get_terms_from_query(
            self.db.query(func.querytree(self.get_tsquery())).first()
        )
        highlight_terms = set()
        with BIN_Db.get_db() as bindb:
            for term in index_terms:
                highlight_terms.update(get_wordforms(bindb, term))
        return highlight_terms

    def get_document(self, minute: Minute) -> str:
        return Markup.escape(
            "\n".join(part for part in (minute.inquiry, minute.remarks,) if part)
        )

    def get_preview(self, document: Markup, highlight_terms: Set[str]) -> Markup:
        def repl(matchobj):
            match = matchobj.group(0)
            if match.lower() in highlight_terms:
                return Markup(f"<em>{match}</em>")
            return match

        preview = re.sub(r"\w+", repl, str(document))
        return Markup(preview)

    def __iter__(self):
        highlight_terms = self.get_highlight_terms()
        for minute in self.page:
            document = self.get_document(minute)
            preview = self.get_preview(document, highlight_terms)
            yield minute, preview
