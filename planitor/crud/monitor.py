from typing import Tuple

from sqlalchemy.orm import Session

from planitor.language.search import lemmatize_query
from planitor.models import Subscription, SubscriptionTypeEnum, User


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
