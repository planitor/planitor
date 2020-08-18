import sqlalchemy
from sqlalchemy import and_, func


def column_windows(session, column, windowsize, reverse=False):
    """Return a series of WHERE clauses against
    a given column that break it into windows.

    Result is an iterable of tuples, consisting of
    ((start, end), whereclause), where (start, end) are the ids.

    Requires a database that supports window functions,
    i.e. Postgresql, SQL Server, Oracle.

    Enhance this yourself !  Add a "where" argument
    so that windows of just a subset of rows can
    be computed.

    """

    def int_for_range(start_id, end_id):
        if end_id:
            return and_(column >= start_id, column < end_id)
        else:
            return column >= start_id

    if reverse:
        order_by = column.desc()
    else:
        order_by = column

    q = session.query(
        column, func.row_number().over(order_by=order_by).label("rownum")
    ).from_self(column)
    if windowsize > 1:
        q = q.filter(sqlalchemy.text("rownum %% %d=1" % windowsize))

    intervals = [id for id, in q]

    while intervals:
        start = intervals.pop(0)
        if intervals:
            end = intervals[0]
        else:
            end = None
        yield int_for_range(start, end)


def windowed_query(q, column, windowsize, reverse=False):
    """"Break a Query into windows on a given column."""

    if reverse:
        order_by = column.desc()
    else:
        order_by = column

    for whereclause in column_windows(q.session, column, windowsize):
        for row in q.filter(whereclause).order_by(order_by):
            yield row
