from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from typing import List

from planitor.database import get_db
from planitor import models
from planitor.schemas.monitor import Subscription, SubscriptionForm
from planitor.security import get_current_active_user

router = APIRouter()


@router.get("/me/subscriptions", response_model=List[Subscription])
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


@router.post("/me/subscriptions", response_model=Subscription)
def create_subscription():
    return None


@router.post("/me/subscriptions/{id}", response_model=Subscription)
def update_subscription(
    id: int,
    request: Request,
    form: SubscriptionForm,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscription = db.query(models.Subscription).get(id)
    if subscription is None or subscription.user != current_user:
        return HTTPException(404)
    subscription.active = form.active
    subscription.immediate = form.immediate
    db.add(subscription)
    db.commit()
    return subscription
