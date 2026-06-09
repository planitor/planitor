from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from planitor.database import get_async_db
from planitor.mail import get_html
from planitor.monitor import iter_user_meeting_deliveries, iter_user_weekly_deliveries

router = APIRouter()


@router.get("/mail/subscription_weekly.html")
async def _mail_debug_weekly(db: AsyncSession = Depends(get_async_db)) -> Response:
    html = "asdf"
    html = await db.run_sync(_render_weekly_debug_email, html)
    return Response(html, media_type="text/html")


@router.get("/mail/subscription_meeting.html")
async def _mail_debug_meeting(db: AsyncSession = Depends(get_async_db)) -> Response:
    html = "Empty"
    html = await db.run_sync(_render_meeting_debug_email, html)
    return Response(html, media_type="text/html")


def _render_weekly_debug_email(db, html):
    for _, meeting_minute_deliveries in iter_user_weekly_deliveries(db):
        html = get_html(
            "subscription_weekly.html",
            {"meeting_minute_deliveries": meeting_minute_deliveries},
        )
    return html


def _render_meeting_debug_email(db, html):
    for _, meeting, minute_deliveries in iter_user_meeting_deliveries(db):
        html = get_html(
            "subscription_meeting.html",
            {"minute_deliveries": minute_deliveries, "meeting": meeting},
        )
    return html
