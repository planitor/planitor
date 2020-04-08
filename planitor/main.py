import datetime as dt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import hashids as h
from .meetings import MeetingView
from .models import Municipality, Meeting, Minute, Case, Entity
from .database import get_db
from .utils.timeago import timeago
from .mapkit import get_token as mapkit_get_token


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


@app.get("/s/{muni_slug}")
async def get_municipality(
    request: Request, muni_slug: str, page: str = None, db: Session = Depends(get_db)
):
    muni = db.query(Municipality).filter_by(slug=muni_slug).first()
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


@app.get("/s/{muni_slug}/{council_slug}/fundir/{meeting_id}")
async def get_meeting(
    request: Request,
    muni_slug: str,
    council_slug: str,
    meeting_id: str,
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).get(h.decode(meeting_id)[0])
    if (
        meeting is None
        or meeting.council.council_type.value.slug != council_slug
        or meeting.council.municipality.slug != muni_slug
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
            "council": meeting.council,
            "meeting": meeting,
            "minutes": minutes,
            "request": request,
        },
    )


@app.get("/s/{muni_slug}/{council_slug}")
async def get_council(
    request: Request, muni_slug: str, council_slug: str, db: Session = Depends(get_db),
):
    return None


@app.get("/s/{muni_slug}/{council_slug}/verk/{case_id}")
async def get_case(
    request: Request,
    muni_slug: str,
    council_slug: str,
    case_id: str,
    db: Session = Depends(get_db),
):
    case_id = h.decode(case_id)
    if not case_id:
        raise HTTPException(status_code=404, detail="Verk fannst ekki")
    case = db.query(Case).get(case_id[0])
    if (
        case is None
        or case.council.council_type.value.slug != council_slug
        or case.council.municipality.slug != muni_slug
    ):
        raise HTTPException(status_code=404, detail="Verk fannst ekki")

    minutes = (
        db.query(Minute)
        .join(Meeting)
        .filter(Minute.case_id == case.id)
        .order_by(Meeting.start)
    )
    return templates.TemplateResponse(
        "case.html",
        {
            "municipality": case.council.municipality,
            "case": case,
            "council": case.council,
            "minutes": minutes,
            "request": request,
        },
    )


def _get_entity(db, kennitala, slug) -> Entity:
    entity = db.query(Entity).filter(Entity.kennitala == kennitala).first()
    if entity is None or (slug is not None and entity.slug != slug):
        raise HTTPException(status_code=404, detail="Kennitala fannst ekki")
    return entity


@app.get("/f/{kennitala}")
@app.get("/f/{slug}-{kennitala}")
async def get_company(
    request: Request, kennitala: str, slug: str = None, db: Session = Depends(get_db),
):
    entity = _get_entity(db, kennitala, slug)
    if slug is None:
        return RedirectResponse("/f/{}-{}".format(entity.slug, entity.kennitala))
    return templates.TemplateResponse(
        "company.html", {"entity": entity, "request": request}
    )


@app.get("/p/{kennitala}")
@app.get("/p/{slug}-{kennitala}")
async def get_person(
    request: Request, kennitala: str, slug: str = None, db: Session = Depends(get_db),
):
    entity = _get_entity(db, kennitala, slug)
    if slug is None:
        return RedirectResponse("/p/{}-{}".format(entity.slug, entity.kennitala))
    return templates.TemplateResponse(
        "person.html", {"entity": entity, "request": request}
    )


@app.get("/mapkit-token")
async def mapkit_token(request: Request):
    return PlainTextResponse(mapkit_get_token())
