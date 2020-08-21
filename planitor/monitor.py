"""

Users are able to monitor

    a) cases,
    b) addresses (+radius),
    c) entities
    d) search terms

In all cases the user can choose to get immediate delivery or stash notifications
together into a weekly friday combined email.

https://dramatiq.io/cookbook.html#composition

"""

from typing import Iterator

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from planitor.models import Case, Minute, Subscription, Address


def match_minute(db: Session, minute: Minute) -> Iterator[Subscription]:

    filters = (
        Subscription.id == 0
    )  # Start a false-y filter to use the or-pipe operator on

    kennitalas = [e.entity_id for e in minute.case.entities]

    assert minute.search_vector or minute.case or kennitalas, minute.case.iceaddr

    if minute.search_vector:

        sq = db.query(Minute.search_vector).filter(Minute.id == minute.id).subquery()

        filters = filters | and_(
            Subscription.search_lemmas != None,  # noqa
            sq.c.search_vector.op("@@")(
                func.websearch_to_tsquery("simple", Subscription.search_lemmas)
            ),
        )

    if minute.case:
        filters = filters | (Subscription.case == minute.case)

    if kennitalas:
        filters = filters | (Subscription.entity_kennitala.in_(kennitalas))

    address = minute.case.iceaddr

    if address:
        filters = filters | (Subscription.address_hnitnum == minute.case.address_id)

        lat, lon = address.lat_wgs84, address.long_wgs84
        if lat and lon:
            filters = filters | (
                (
                    func.earth_distance(
                        func.ll_to_earth(lat, lon),
                        func.ll_to_earth(Address.lat_wgs84, Address.long_wgs84),
                    )
                    < Subscription.radius
                )
            )

    query = (
        db.query(Subscription)
        .select_from(Subscription)
        .outerjoin(Case)
        .outerjoin(Address, Address.hnitnum == Subscription.address_hnitnum)
        .filter(Subscription.active == True)  # noqa
        .filter(filters)
    )

    yield from query
