from typing import Tuple

from sqlalchemy.orm import Session

from planitor.models import (
    User,
    Case,
    Subscription,
    SubscriptionTypeEnum,
    Address,
    Delivery,
    Minute,
    Entity,
)

from planitor.language.search import lemmatize_query


def get_or_create_search_subscription(
    db: Session, user: User, search_query: str
) -> Tuple[Subscription, bool]:
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user == user, Subscription.search_query == search_query)
        .first()
    )

    created = bool(subscription)

    if subscription is None:
        subscription = Subscription(
            user=user,
            search_query=search_query,
            search_lemmas=lemmatize_query(search_query).lower(),
            type=SubscriptionTypeEnum.search,
        )
        db.add(subscription)

    return subscription, created


def create_delivery(db: Session, subscription: Subscription, minute: Minute) -> Delivery:
    delivery = Delivery(subscription=subscription, minute=minute)
    db.add(delivery)
    return delivery


def get_delivery(db: Session, subscription: Subscription, minute: Minute) -> Delivery:
    delivery = (
        db.query(Delivery)
        .filter(Delivery.subscription == subscription, Delivery.minute == minute)
        .first()
    )
    return delivery


def get_case_subscription(db: Session, user: User, case: Case):
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.case == case,
            Subscription.user == user,
            Subscription.type == SubscriptionTypeEnum.case,
        )
        .first()
    )
    return subscription


def get_address_subscription(db: Session, user: User, address: Address):
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.address == address,
            Subscription.user == user,
            Subscription.type == SubscriptionTypeEnum.address,
        )
        .first()
    )
    return subscription


def get_entity_subscription(db: Session, user: User, entity: Entity):
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.entity == entity,
            Subscription.user == user,
            Subscription.type == SubscriptionTypeEnum.entity,
        )
        .first()
    )
    return subscription


def create_case_subscription(db: Session, user: User, case: Case):
    subscription = get_case_subscription(db, user, case)
    if subscription is None:
        subscription = Subscription(case=case, user=user, type=SubscriptionTypeEnum.case)
        db.add(subscription)
        db.commit()
    return subscription


def create_entity_subscription(db: Session, user: User, entity: Entity):
    subscription = get_entity_subscription(db, user, entity)
    if subscription is None:
        subscription = Subscription(
            entity=entity, user=user, type=SubscriptionTypeEnum.entity
        )
        db.add(subscription)
        db.commit()
    return subscription


def create_address_subscription(db: Session, user: User, address: Address):
    subscription = get_address_subscription(db, user, address)
    if subscription is None:
        subscription = Subscription(
            address=address, user=user, type=SubscriptionTypeEnum.address
        )
        db.add(subscription)
        db.commit()
    return subscription


def delete_subscription(db: Session, subscription: Subscription) -> None:
    # Set archival values for deliveries and remove subscription foreign key
    db.query(Delivery).filter(Delivery.subscription == subscription).update(
        {
            Delivery.subscription_id: None,
            Delivery.deleted_subscription_id: subscription.id,
            Delivery.deleted_user_id: subscription.user.id,
        }
    )
    db.delete(subscription)
    db.commit()


def delete_case_subscription(db: Session, user: User, case: Case):
    subscription = get_case_subscription(db, user, case)
    if subscription is None:
        return None
    delete_subscription(db, subscription)


def delete_entity_subscription(db: Session, user: User, entity: Entity):
    subscription = get_entity_subscription(db, user, entity)
    if subscription is None:
        return None
    delete_subscription(db, subscription)


def delete_address_subscription(db: Session, user: User, address: Address):
    subscription = get_address_subscription(db, user, address)
    if subscription is None:
        return None
    delete_subscription(db, subscription)
