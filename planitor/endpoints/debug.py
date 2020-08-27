from fastapi import APIRouter, Depends, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from planitor.mail import get_html

from planitor.database import get_db
from planitor.models import (
    Entity,
    Subscription,
    User,
    Case,
    Minute,
    Delivery,
    SubscriptionTypeEnum,
)

router = APIRouter()


@router.get("/mail/subscription_immediate.html")
def _mail_debug(db: Session = Depends(get_db)) -> Response:
    user = db.query(User).order_by(func.random()).first()
    minute = (
        db.query(Minute)
        .join(Case)
        .filter(Case.iceaddr != None)
        .order_by(func.random())
        .first()
    )
    delivery = Delivery(
        subscription=Subscription(
            user=user,
            type=SubscriptionTypeEnum.radius,
            radius=200,
            address=minute.case.iceaddr,
        ),
        minute=minute,
    )
    html = get_html(
        "subscription_immediate.html",
        {"delivery": delivery, "email_to": "jokull@solberg.is"},
    )
    return Response(html, media_type="text/html")


@router.get("/mail/subscription_weekly.html")
def _mail_debug_weekly(db: Session = Depends(get_db)) -> Response:
    user = db.query(User).order_by(func.random()).first()
    entity = db.query(Entity).order_by(func.random()).first()
    minute = (
        db.query(Minute)
        .join(Case)
        .filter(Case.iceaddr != None)
        .order_by(func.random())
        .first()
    )
    deliveries = [
        Delivery(
            subscription=Subscription(
                user=user, type=SubscriptionTypeEnum.entity, entity=entity,
            ),
            minute=(
                db.query(Minute)
                .join(Case)
                .filter(Case.iceaddr != None)
                .order_by(func.random())
                .first()
            ),
        ),
        Delivery(
            subscription=Subscription(
                user=user,
                type=SubscriptionTypeEnum.radius,
                radius=200,
                address=minute.case.iceaddr,
            ),
            minute=minute,
        ),
    ]
    html = get_html("subscription_weekly.html", {"deliveries": deliveries},)
    return Response(html, media_type="text/html")
