from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import hashids as h
from .models import Municipality, Council, Meeting, Minute
from .database import get_db
from .utils.timeago import timeago


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals.update({"h": h, "timeago": timeago})


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
    request: Request, muni_id: str, db: Session = Depends(get_db)
):
    muni = db.query(Municipality).get(h.decode(muni_id)[0])
    if muni is None:
        raise HTTPException(status_code=404, detail="Sveitarfélag fannst ekki")

    sq = db.query(Minute).subquery()
    meetings = (
        db.query(Meeting, func.count(sq.c.id))
        .join(Council)
        .join(sq, Meeting.id == sq.c.meeting_id)
        .filter(Council.municipality_id == muni.id)
        .group_by(Meeting.id)
        .order_by(Meeting.start.desc())
    )
    return templates.TemplateResponse(
        "municipality.html",
        {"municipality": muni, "meetings": meetings, "request": request},
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
        or meeting.council_type.value.slug != council_slug
        or meeting.council.municipality_id != h.decode(muni_id)[0]
    ):
        raise HTTPException(status_code=404, detail="Fundargerð fannst ekki")
    minutes = (
        db.query(Minute)
        .filter(Minute.meeting_id == meeting.id)
        .order_by(Meeting.start.desc())
    )
    return templates.TemplateResponse(
        "municipality.html",
        {
            "municipality": meeting.council.muni,
            "meeting": meeting,
            "minutes": minutes,
            "request": request,
        },
    )
