from fastapi import APIRouter, Depends, Request, Response
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
    if form.active is not None:
        subscription.active = form.active
    if form.immediate is not None:
        subscription.immediate = form.immediate
    if form.radius is not None:
        subscription.radius = form.radius
    db.add(subscription)
    db.commit()
    return subscription


@router.delete("/me/subscriptions/{id}")
def delete_subscription(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscription = db.query(models.Subscription).get(id)
    if subscription is None or subscription.user != current_user:
        return HTTPException(404)

    # Set archival values for deliveries and remove subscription foreign key
    db.query(models.Delivery).filter(models.Delivery.subscription == subscription).update(
        {
            models.Delivery.subscription_id: None,
            models.Delivery.deleted_subscription_id: subscription.id,
            models.Delivery.deleted_user_id: subscription.user.id,
        }
    )
    db.delete(subscription)
    db.commit()
    return Response(None, 204)
