from sqlalchemy import func
from sqlakeyset import get_page

from .models import CaseStatusEnum, Minute, Meeting, Council


class MeetingWrap:
    """ Thin wrapper around Meeting objects. Attribute are passed to the `_meeting`
    object so that it acts like the wrapped object with the `counts` attribute added.

    """

    def __init__(self, meeting, counts):
        self._meeting = meeting
        self.counts = dict(zip((enum for enum in ENUMS), counts))
        self.year = meeting.start.year

    def __getattribute__(self, key):
        if key != "_meeting" and hasattr(self._meeting, key):
            return getattr(self._meeting, key)
        return super().__getattribute__(key)

    @property
    def minute_count(self):
        return sum(self.counts.values())

    @property
    def folded_counts(self):
        """ Condense statuses to approve/denied/other """
        counts = self.counts.copy()
        none = NoneEnum()
        folded = {CaseStatusEnum.approved: 0, CaseStatusEnum.denied: 0, none: 0}
        for enum in CaseStatusEnum:
            count = counts.pop(enum)
            if count is not None:
                if enum in (CaseStatusEnum.approved, CaseStatusEnum.denied):
                    folded[enum] = count
                else:
                    folded[none] += count
        return folded


class NoneEnum:
    name = "other"
    value = {"label": "Annað"}


ENUMS = list(CaseStatusEnum) + [NoneEnum()]


class MeetingView:
    """ Wraps a meeting query that number of each type of minute. This is useful to
    display an stream of meetings in a card or table layout with useful metadata.
    Queries are constructed by iterating through an enum, applying an outerjoin
    subquery with a count for each enum value. The query results are wrapped in
    instances of the `MeetingWrap` class for better accessing of the counter values.

    What’s cool is that no enums are hardcoded.

    Usage:

    >>> for meeting in MeetingView(db, offset=0, limit=100):
    >>>     print(meeting.name, meeting.counter[CaseStatusEnum.delayed])

    This would give you a list of meetings along with number of minutes where the
    status was `delayed`.

    """

    PER_PAGE = 20

    def __init__(self, db, page_bookmark, *filters):
        self.db = db
        self.page_bookmark = page_bookmark

        def get_sq(enum):
            return (
                self.db.query(
                    func.count(Minute.id).label("count"),
                    Minute.meeting_id.label("meeting_id"),
                )
                .filter(Minute.status == (None if isinstance(enum, NoneEnum) else enum))
                .group_by(Minute.meeting_id)
            ).subquery(enum.name)

        sqs = [(get_sq(enum), enum) for enum in ENUMS]

        query = db.query(Meeting).select_from(Meeting).join(Council)
        for sq, enum in sqs:
            query = query.outerjoin(sq, sq.c.meeting_id == Meeting.id).add_columns(
                func.coalesce(sq.c.count, 0).label(enum.name)
            )
        query = query.filter(*filters)
        query = query.order_by(Meeting.start.desc())

        self.query = query
        self.page = get_page(query, per_page=self.PER_PAGE, page=page_bookmark)
        self.paging = self.page.paging

    def __iter__(self):
        for meeting, *counts in self.page:
            yield MeetingWrap(meeting, counts)
