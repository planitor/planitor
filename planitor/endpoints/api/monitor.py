from typing import List

from fastapi import Depends, Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from planitor import models
from planitor.crud import monitor as crud
from planitor.database import get_db
from planitor.models.city import CouncilTypeEnum
from planitor.schemas.monitor import (
    Subscription,
    SubscriptionCouncilTypeForm,
    SubscriptionForm,
)
from planitor.security import get_current_active_user

from . import router


@router.get("/subscriptions", response_model=List[Subscription])
def get_subscriptions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscriptions = (
        db.query(models.Subscription)
        .outerjoin(models.Entity)
        .outerjoin(models.Address)
        .outerjoin(models.Case)
        .filter(models.Subscription.user == current_user)
        .order_by(models.Subscription.created)
        .all()
    )
    return subscriptions


@router.post("/subscriptions", response_model=Subscription)
def create_subscription():
    return None


def set_subscription_council_types(
    subscription: models.Subscription,
    council_types: List[SubscriptionCouncilTypeForm],
) -> None:
    """If all councils selected, whether within municipality or the available council
    types, turn field into None, which is the default state. If no councils selected,
    deactivate subscription, but let `councils` field keep the presumable last remaining
    council type, so that when reactivated, that is the selected council."""

    if council_types == []:
        subscription.active = False
        return

    # Turn form into dict with named keys, for easier access
    _types = {c.name for c in council_types}

    municipality = subscription.get_municipality()

    if municipality:
        _municipality_councils = {c.council_type.name for c in municipality.councils}
        all_selected = _municipality_councils.issubset(_types)
        if all_selected:
            subscription.council_types = None
            return

    subscription.council_types = [getattr(CouncilTypeEnum, key) for key in _types]
    if set(subscription.council_types) == set(CouncilTypeEnum):
        subscription.council_types = None


@router.post("/subscriptions/{id}", response_model=Subscription)
def update_subscription(
    id: int,
    request: Request,
    form: SubscriptionForm,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscription = db.query(models.Subscription).get(id)
    if subscription is None or subscription.user != current_user:
        raise HTTPException(404)
    if form.active is not None:
        subscription.active = form.active
    if form.immediate is not None:
        subscription.immediate = form.immediate
    if form.radius is not None:
        subscription.radius = form.radius
    if form.council_types is not None:
        set_subscription_council_types(subscription, form.council_types)
    db.add(subscription)
    db.commit()
    return subscription


@router.delete("/subscriptions/{id}")
def delete_subscription(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscription = db.query(models.Subscription).get(id)
    if subscription is None or subscription.user != current_user:
        raise HTTPException(404)
    crud.delete_subscription(db, subscription)
    return Response(None, 204)
