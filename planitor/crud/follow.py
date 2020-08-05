from sqlalchemy.orm import Session

from planitor.models import User, Case, Subscription, SubscriptionTypeEnum, Address


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


def create_case_subscription(db: Session, user: User, case: Case):
    subscription = get_case_subscription(db, user, case)
    if subscription is None:
        subscription = Subscription(case=case, user=user, type=SubscriptionTypeEnum.case)
        db.add(subscription)
        db.commit()
    return subscription


def delete_case_subscription(db: Session, user: User, case: Case):
    subscription = get_case_subscription(db, user, case)
    if subscription is None:
        return None
    db.delete(subscription)
    db.commit()


def create_address_subscription(db: Session, user: User, address: Address):
    subscription = get_address_subscription(db, user, address)
    if subscription is None:
        subscription = Subscription(
            address=address, user=user, type=SubscriptionTypeEnum.address
        )
        db.add(subscription)
        db.commit()
    return subscription


def delete_address_subscription(db: Session, user: User, address: Address):
    subscription = get_address_subscription(db, user, address)
    if subscription is None:
        return None
    db.delete(subscription)
    db.commit()
