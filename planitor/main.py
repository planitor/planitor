import datetime as dt
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import hashids as h
from .meetings import MeetingView
from .models import Municipality, Meeting, Minute, Case
from .database import get_db
from .utils.timeago import timeago


def human_date(date: dt.datetime) -> str:
    MONTHS = [
        u"janúar",
        u"febrúar",
        u"mars",
        u"apríl",
        u"maí",
        u"júní",
        u"júlí",
        u"ágúst",
        u"september",
        u"október",
        u"nóvember",
        u"desember",
    ]
    return "{}. {}, {}".format(date.day, MONTHS[date.month - 1], date.year)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals.update({"h": h, "timeago": timeago, "human_date": human_date})


@app.get("/")
async def get_index(
    request: Request, db: Session = Depends(get_db),
):
    municipalities = db.query(Municipality)
    return templates.TemplateResponse(
        "index.html", {"municipalities": municipalities, "request": request}
    )


@app.get("/sveitarfelog/{muni_id}")
async def get_municipality(
    request: Request, muni_id: str, page: str = None, db: Session = Depends(get_db)
):
    muni = db.query(Municipality).get(h.decode(muni_id)[0])
    if muni is None:
        raise HTTPException(status_code=404, detail="Sveitarfélag fannst ekki")

    meetings = MeetingView(db, muni, page)

    return templates.TemplateResponse(
        "municipality.html",
        {
            "municipality": muni,
            "meetings": meetings,
            "paging": meetings.paging,
            "request": request,
        },
    )


@app.get("/sveitarfelog/{muni_id}/{council_slug}/{meeting_id}")
async def get_meeting(
    request: Request,
    muni_id: str,
    council_slug: str,
    meeting_id: str,
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).get(h.decode(meeting_id)[0])
    if (
        meeting is None
        or meeting.council.council_type.value.slug != council_slug
        or meeting.council.municipality_id != h.decode(muni_id)[0]
    ):
        raise HTTPException(status_code=404, detail="Fundargerð fannst ekki")
    sq_count = (
        db.query(Case.id, func.count(Minute.id).label("case_count"))
        .join(Minute, Case.id == Minute.case_id)
        .group_by(Case.id)
        .subquery()
    )
    minutes = (
        db.query(Minute, sq_count.c.case_count)
        .select_from(Minute)
        .filter(Minute.meeting_id == meeting.id)
        .join(sq_count, sq_count.c.id == Minute.case_id)
        .order_by(Minute.id)
    )
    return templates.TemplateResponse(
        "meeting.html",
        {
            "municipality": meeting.council.municipality,
            "meeting": meeting,
            "minutes": minutes,
            "request": request,
        },
    )
