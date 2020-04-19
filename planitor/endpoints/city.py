from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.datastructures import Secret

from planitor import hashids, config
from planitor.meetings import MeetingView
from planitor.models import Municipality, Meeting, Minute, Case, Entity
from planitor.database import get_db
from planitor.mapkit import get_token as mapkit_get_token

from .templates import templates


router = APIRouter()


@router.get("/")
async def get_index(
    request: Request, db: Session = Depends(get_db),
):
    municipalities = db.query(Municipality)
    return templates.TemplateResponse(
        "index.html", {"municipalities": municipalities, "request": request}
    )


@router.get("/s/{muni_slug}")
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


@router.get("/s/{muni_slug}/{council_slug}/fundir/{meeting_id}")
async def get_meeting(
    request: Request,
    muni_slug: str,
    council_slug: str,
    meeting_id: str,
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).get(hashids.decode(meeting_id)[0])
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


@router.get("/s/{muni_slug}/{council_slug}")
async def get_council(
    request: Request, muni_slug: str, council_slug: str, db: Session = Depends(get_db),
):
    return None


@router.get("/s/{muni_slug}/{council_slug}/verk/{case_id}")
async def get_case(
    request: Request,
    muni_slug: str,
    council_slug: str,
    case_id: str,
    db: Session = Depends(get_db),
):
    case_id = hashids.decode(case_id)
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


@router.get("/f/{kennitala}")
@router.get("/f/{slug}-{kennitala}")
async def get_company(
    request: Request, kennitala: str, slug: str = None, db: Session = Depends(get_db),
):
    entity = _get_entity(db, kennitala, slug)
    if slug is None:
        return RedirectResponse("/f/{}-{}".format(entity.slug, entity.kennitala))
    return templates.TemplateResponse(
        "company.html", {"entity": entity, "request": request}
    )


@router.get("/p/{kennitala}")
@router.get("/p/{slug}-{kennitala}")
async def get_person(
    request: Request, kennitala: str, slug: str = None, db: Session = Depends(get_db),
):
    entity = _get_entity(db, kennitala, slug)
    if slug is None:
        return RedirectResponse("/p/{}-{}".format(entity.slug, entity.kennitala))
    return templates.TemplateResponse(
        "person.html", {"entity": entity, "request": request}
    )


@router.get("/mapkit-token")
async def mapkit_token(request: Request):
    return PlainTextResponse(
        mapkit_get_token(config("MAPKIT_PRIVATE_KEY", cast=Secret))
    )
