from planitor.models.city import Minute
from sqlalchemy import func
from sqlalchemy.orm.session import Session

from planitor import monitor
from planitor.crud import get_or_create_search_subscription
from planitor.minutes import get_minute_lemmas
from planitor.models import (
    Address,
    CaseEntity,
    Delivery,
    Subscription,
    SubscriptionTypeEnum,
    User,
)
from planitor.monitor import get_unsent_deliveries, _notify_subscribers


def test_match_minute_case(db, minute, case, user):
    subscription = Subscription(user=user, case=case, type=SubscriptionTypeEnum.case)
    db.add(subscription)
    db.commit()
    assert minute.case == subscription.case
    assert list(monitor.match_minute(db, minute)) == [subscription]


def test_match_minute_address(db, minute, user, case):
    subscription = Subscription(
        user=user, address=case.iceaddr, type=SubscriptionTypeEnum.address
    )
    db.add(subscription)
    db.commit()
    assert list(monitor.match_minute(db, minute)) == [subscription]


# Two points with 117.8m distance between them
KRAMBUD = 64.1337021, -21.9095417
LANGAHLID = 64.133129, -21.911580


def test_match_minute_radius(db, minute, user):

    lat, lon = KRAMBUD
    address_1 = Address(hnitnum=2, lat_wgs84=lat, long_wgs84=lon)
    db.add(address_1)

    lat, lon = LANGAHLID
    address_2 = Address(hnitnum=3, lat_wgs84=lat, long_wgs84=lon)
    db.add(address_2)

    minute.case.iceaddr = address_2
    db.add(minute.case)
    db.commit()
    subscription = Subscription(
        user=user, address=address_1, type=SubscriptionTypeEnum.address, radius=100
    )
    db.add(subscription)
    db.commit()
    assert list(monitor.match_minute(db, minute)) == []

    subscription.radius = 200
    db.add(subscription)
    db.commit()
    assert list(monitor.match_minute(db, minute)) == [subscription]


def test_match_minute_entity(db, minute, user, company):
    subscription = Subscription(
        user=user, entity=company, type=SubscriptionTypeEnum.entity
    )
    minute.case.entities.append(CaseEntity(case_id=minute.case.id, entity=company))
    db.add(minute.case)
    db.add(subscription)
    db.commit()
    assert list(monitor.match_minute(db, minute)) == [subscription]


def test_match_minute_search_no_match(db, minute, user):
    minute.headline = "Klæða gips á hús"
    lemmas = get_minute_lemmas(minute)
    minute.search_vector = func.to_tsvector("simple", " ".join(lemmas))
    get_or_create_search_subscription(db, user, "álplata")
    db.commit()
    assert list(monitor.match_minute(db, minute)) == []


def test_match_minute_search(db, minute, user):
    minute.headline = "Klæða álplötur á hús"
    lemmas = get_minute_lemmas(minute)
    minute.search_vector = func.to_tsvector("simple", " ".join(lemmas))
    subscription, _ = get_or_create_search_subscription(db, user, "álplata")
    db.commit()
    assert list(monitor.match_minute(db, minute)) == [subscription]


def test_get_unsent_deliveries(db: Session, user, case, meeting, minute, subscription):
    # User has one subscription/delivery, User 2 has two subscriptions/deliveries
    user_2 = User(email="foo")
    subscription_2 = Subscription(user=user_2, case=case, type=SubscriptionTypeEnum.case)
    delivery_1 = Delivery(minute=minute, subscription=subscription)
    delivery_2a = Delivery(minute=minute, subscription=subscription_2)
    delivery_2b = Delivery(
        minute=Minute(case=case, meeting=meeting), subscription=subscription_2
    )
    db.add_all([user_2, delivery_1, subscription_2, delivery_2a, delivery_2b])
    db.commit()

    results = []
    for _user, _deliveries in get_unsent_deliveries(db):
        results.append((_user, set(_deliveries)))

    assert results == [
        (
            user,
            {
                delivery_1,
            },
        ),
        (user_2, {delivery_2a, delivery_2b}),
        #
    ]


def test_notify_subscribers(
    db: Session, user, case, minute, subscription, emails_message_send
):
    """Test that ensures that users are not notified multiple times for the same
    minute."""

    # Create another subscription for the same user that captures the same minute
    subscription_2 = Subscription(
        user=user, address=case.iceaddr, type=SubscriptionTypeEnum.address
    )
    db.add(subscription_2)

    # Create another user and subscription for the same minute
    user_2 = User(email="user_2@bar.com")
    subscription_3 = Subscription(
        user=user_2, address=case.iceaddr, type=SubscriptionTypeEnum.address
    )
    db.add(user_2)
    db.add(subscription_3)
    db.commit()

    deliveries = list(_notify_subscribers(db, minute))
    assert emails_message_send.call_count == 2
    assert {user_2.email, user.email} == {
        call_args.kwargs["to"] for call_args in emails_message_send.call_args_list
    }
    assert len(deliveries) == 3
