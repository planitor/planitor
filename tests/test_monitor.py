from sqlalchemy import func

from planitor import monitor
from planitor.models import Subscription, SubscriptionTypeEnum, Address, CaseEntity
from planitor.minutes import get_minute_lemmas
from planitor.crud import get_or_create_search_subscription


def test_match_minute_case(db, minute, case, user):
    subscription = Subscription(user=user, case=case, type=SubscriptionTypeEnum.case)
    db.add(subscription)
    db.commit()
    assert minute.case == subscription.case
    assert list(monitor.match_minute(db, minute)) == [subscription]


def test_match_minute_address(db, minute, user):
    address = Address(hnitnum=1)
    db.add(address)
    minute.case.iceaddr = address
    db.add(minute.case)
    db.commit()
    subscription = Subscription(
        user=user, address=address, type=SubscriptionTypeEnum.address
    )
    db.add(subscription)
    db.commit()
    assert list(monitor.match_minute(db, minute)) == [subscription]


# Two points with 117.8m distance between them
KRAMBUD = 64.1337021, -21.9095417
LANGAHLID = 64.133129, -21.911580


def test_match_minute_radius(db, minute, user):

    lat, lon = KRAMBUD
    address_1 = Address(hnitnum=1, lat_wgs84=lat, long_wgs84=lon)
    db.add(address_1)

    lat, lon = LANGAHLID
    address_2 = Address(hnitnum=2, lat_wgs84=lat, long_wgs84=lon)
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
    subscription, _ = get_or_create_search_subscription(db, user, "álplata")
    db.commit()
    assert list(monitor.match_minute(db, minute)) == []


def test_match_minute_search(db, minute, user):
    minute.headline = "Klæða álplötur á hús"
    lemmas = get_minute_lemmas(minute)
    minute.search_vector = func.to_tsvector("simple", " ".join(lemmas))
    subscription, _ = get_or_create_search_subscription(db, user, "álplata")
    db.commit()
    assert list(monitor.match_minute(db, minute)) == [subscription]
