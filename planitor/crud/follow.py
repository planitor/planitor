from sqlalchemy.orm import Session

from planitor.models import User, Case, Subscription, SubscriptionTypeEnum


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
