from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from planitor.database import get_db
from planitor.mail import get_html
from planitor.monitor import iter_user_meeting_deliveries, iter_user_weekly_deliveries

router = APIRouter()


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
