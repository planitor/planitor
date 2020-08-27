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

from typing import Iterable, Iterator, Tuple
from itertools import groupby

import dramatiq
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from planitor.crud import create_delivery
from planitor.database import db_context
from planitor.mail import send_email
from planitor.models import Address, Case, Delivery, Meeting, Minute, Subscription, User


def match_minute(db: Session, minute: Minute) -> Iterator[Subscription]:

    filters = (
        Subscription.id == 0
    )  # Start a false-y filter to use the or-pipe operator on

    kennitalas = [e.entity_id for e in minute.case.entities]

    assert minute.search_vector or minute.case or kennitalas

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

    if kennitalas:
        filters = filters | (Subscription.entity_kennitala.in_(kennitalas))

    query = (
        db.query(Subscription)
        .select_from(Subscription)
        .outerjoin(Case)
        .outerjoin(Address, Address.hnitnum == Subscription.address_hnitnum)
        .filter(Subscription.active == True)  # noqa
        .filter(filters)
    )

    yield from query


def send_immediate_email(email_to: str, delivery: Delivery) -> None:
    return send_email(
        # email_to,
        "gudmundur@planitor.io",
        str(delivery.minute.case.address or delivery.minute.headline),
        "subscription_immediate.html",
        {"delivery": delivery},
    )


def send_weekly_email(email_to: str, deliveries: Iterable[Delivery]) -> None:
    return send_email(
        # email_to,
        "gudmundur@planitor.io",
        "Vikuleg samantekt",
        "subscription_weekly.html",
        {"deliveries": deliveries},
    )


def _notify_subscribers(db, minute):
    for subscription in match_minute(db, minute):
        delivery = create_delivery(db, subscription, minute)
        delivery.sent = subscription.immediate
        db.commit()
        if delivery.sent:
            send_immediate_email(subscription.user.email, delivery)


@dramatiq.actor
def notify_subscribers(minute_id: int):
    with db_context() as db:
        minute = db.query(Minute).get(minute_id)
        _notify_subscribers(db, minute)


def get_weekly_subscribers(db) -> Iterable[Tuple[User, Iterable[Delivery]]]:
    deliveries = (
        db.query(Delivery)
        .join(Subscription)
        .join(User)
        .join(Minute)
        .join(Meeting)
        .filter(Delivery.sent == False)  # noqa
        .order_by(Subscription.user_id, Meeting.start)
    )
    return groupby(deliveries, key=lambda delivery: delivery.subscription.user)


def _notify_weekly_subscribers(db):
    for user, deliveries in get_weekly_subscribers(db):
        send_weekly_email(user.email, deliveries)


def notify_weekly_subscribers():
    with db_context() as db:
        _notify_weekly_subscribers(db)
