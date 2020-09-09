from itertools import groupby

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
from planitor.monitor import iter_user_meeting_deliveries, iter_user_weekly_deliveries

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
    html = "asdf"
    for _, meeting_minute_deliveries in iter_user_weekly_deliveries(db):
        html = get_html(
            "subscription_weekly.html",
            {"meeting_minute_deliveries": meeting_minute_deliveries},
        )
    return Response(html, media_type="text/html")


@router.get("/mail/subscription_meeting.html")
def _mail_debug_meeting(db: Session = Depends(get_db)) -> Response:
    html = "Empty"
    for _, meeting, minute_deliveries in iter_user_meeting_deliveries(db):
        html = get_html(
            "subscription_meeting.html",
            {"minute_deliveries": minute_deliveries, "meeting": meeting},
        )
    return Response(html, media_type="text/html")
