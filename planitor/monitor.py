"""

Users are able to monitor

    a) cases,
    b) addresses (+radius),
    c) entities
    d) search terms

In all cases the user can choose to get immediate delivery or stash notifications
together into a weekly friday combined email.

https://dramatiq.io/cookbook.html#composition

Immediate deliveries are not immediate in the sense that as soon as we process a minute
we send an email, but that as soon as Planitor picks up a new meeting, we process the
minutes, run the matcher to see who is interested in what minutes, then compile emails
per meeting with all the notes, along with minute-footers explaining which subscriptions
had picked up the note, so the user can tweak their monitoring.

"""

from typing import Iterable, Iterator, Tuple
from itertools import groupby

import dramatiq
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import any_
from sentry_sdk import capture_exception

from planitor.crud import create_delivery, get_delivery
from planitor.database import db_context
from planitor import mail
from planitor.models import Address, Case, Delivery, Meeting, Minute, Subscription, User


MinuteDeliveries = Iterable[Tuple[Minute, Iterable[Delivery]]]


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
            filters = filters | (Subscription.address == minute.case.iceaddr)

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
        # No `subscription_councils` means it should match all of them, the UI masks this
        # by rendering checked checkboxes for all options - when one is unchecked the
        # other rows will appear.
        .filter(
            (minute.meeting.council_type == any_(Subscription.council_types))
            | (Subscription.council_types == None)
        )
        .filter(filters)
    )

    yield from query


def get_unsent_query(db: Session, immediate: bool):
    return (
        db.query(Delivery)
        .join(Subscription)
        .join(Minute, Delivery.minute_id == Minute.id)
        .join(Meeting, Minute.meeting_id == Meeting.id)
        .join(Case, Minute.case_id == Case.id)
        .filter(
            Delivery.sent == None,  # noqa
            Subscription.active == True,
            Subscription.immediate == immediate,
        )
        .order_by(Subscription.user_id, Meeting.id, Delivery.minute_id)
    )


def get_unsent_deliveries(
    db, immediate: bool
) -> Iterable[Tuple[User, Iterable[Delivery]]]:
    return groupby(
        get_unsent_query(db, immediate=immediate),
        key=lambda delivery: delivery.subscription.user,
    )


def _create_deliveries(db: Session, minute: Minute) -> Iterable[Delivery]:
    for subscription in match_minute(db, minute):
        # This result-set could be [sub{u=1}, sub{u=1}, sub{u=2}]. The user probably does
        # not want multiple emails for the same minute because multiple subscribers
        # matched it. Therefore we create deliveries but only deliver the first one.
        if get_delivery(db, subscription, minute):
            # Cannot recreate this subscription/minute combo because of unique constraint
            # - but this state should not be reached unless a worker fails and is retrying
            continue
        delivery = create_delivery(db, subscription, minute)
        yield delivery


@dramatiq.actor
def create_deliveries(minute_id: int):
    with db_context() as db:
        try:
            minute = db.query(Minute).get(minute_id)
            assert minute
            for delivery in _create_deliveries(db, minute):
                db.commit()
        except Exception as e:
            capture_exception(e)
            raise


def iter_user_meeting_deliveries(
    db: Session,
) -> Iterable[Tuple[User, Meeting, MinuteDeliveries]]:
    for user, deliveries in get_unsent_deliveries(db, immediate=True):
        deliveries = list(deliveries)
        for meeting, deliveries in groupby(deliveries, key=lambda d: d.minute.meeting):
            deliveries = list(deliveries)
            yield user, meeting, [
                (minute, list(_deliveries))
                for minute, _deliveries in groupby(deliveries, lambda d: d.minute)
            ]


def send_meeting_email(user: User, meeting: Meeting, minute_deliveries: MinuteDeliveries):
    return mail.send_email(
        user.email,
        str(meeting),
        "subscription_meeting.html",
        {"minute_deliveries": minute_deliveries, "meeting": meeting},
    )


def _send_meeting_emails(db: Session):
    for user, meeting, minute_deliveries in iter_user_meeting_deliveries(db):
        try:
            smtp_response = send_meeting_email(user, meeting, minute_deliveries)
        except Exception as e:
            capture_exception(e)
            continue
        for _, deliveries in minute_deliveries:
            for delivery in deliveries:
                delivery.sent = func.now()
                delivery.mail_confirmation = str(smtp_response)
                db.add(delivery)
        db.commit()


@dramatiq.actor
def send_meeting_emails():
    """As you can see in `scrape.pipelines` both `update_minute_search_vector`
    and `create_deliveries` for each minute are strung into one big pipeline,
    then appended with this task in order to only send one email to each user
    for all their subscriptions per meeting."""
    with db_context() as db:
        _send_meeting_emails(db)


def send_weekly_email(
    user: User, meeting_minute_deliveries: Iterable[Tuple[Meeting, MinuteDeliveries]]
):
    return mail.send_email(
        user.email,
        "Vikuleg samantekt",
        "subscription_weekly.html",
        {"meeting_minute_deliveries": meeting_minute_deliveries},
    )


def iter_user_weekly_deliveries(
    db: Session,
) -> Iterable[Tuple[User, Iterable[Tuple[Meeting, MinuteDeliveries]]]]:
    for user, deliveries in get_unsent_deliveries(db, immediate=False):
        deliveries = list(deliveries)
        meeting_minute_deliveries = []
        for meeting, deliveries in groupby(deliveries, key=lambda d: d.minute.meeting):
            deliveries = list(deliveries)
            minute_deliveries = [
                (minute, list(deliveries))
                for minute, deliveries in groupby(deliveries, lambda d: d.minute)
            ]
            meeting_minute_deliveries.append((meeting, minute_deliveries))
        yield user, meeting_minute_deliveries


def _send_weekly_emails(db: Session):
    for user, meeting_minute_deliveries in iter_user_weekly_deliveries(db):
        try:
            smtp_response = send_weekly_email(user, meeting_minute_deliveries)
        except Exception as e:
            capture_exception(e)
            continue
        for _, minute_deliveries in meeting_minute_deliveries:
            for _, deliveries in minute_deliveries:
                for delivery in deliveries:
                    delivery.sent = func.now()
                    delivery.mail_confirmation = str(smtp_response)
                    db.add(delivery)
        db.commit()


@dramatiq.actor
def send_weekly_emails():
    with db_context() as db:
        _send_weekly_emails(db)
