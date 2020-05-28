from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy import func, extract, distinct
from sqlalchemy.orm import Session
from starlette.datastructures import Secret
from starlette.requests import Request

from planitor import config, hashids
from planitor.database import get_db
from planitor.mapkit import get_token as mapkit_get_token
from planitor.meetings import MeetingView
from planitor.models import (
    Case,
    Entity,
    Meeting,
    Minute,
    Municipality,
    User,
    Council,
    CouncilTypeEnum,
)
from planitor.security import get_current_active_user_or_none
from planitor.search import MinuteResults

from .templates import templates

router = APIRouter()


@router.get("/leit")
async def get_search(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
    q: str = "",
    page: int = 1,
) -> templates.TemplateResponse:
    if q:
        results = MinuteResults(db, q, page)
    else:
        results = None

    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "q": q, "user": current_user, "results": results},
    )


@router.get("/s")
async def get_index():
    return RedirectResponse("/s/reykjavik")


@router.get("/s/{muni_slug}")
@router.get("/s/{muni_slug}/{council_slug}")
async def get_municipality(
    request: Request,
    muni_slug: str,
    council_slug: str = None,
    page: str = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    muni = db.query(Municipality).filter(Municipality.slug == muni_slug).first()
    if muni is None:
        raise HTTPException(status_code=404, detail="Sveitarfélag fannst ekki")

    councils = db.query(Council).filter(Council.municipality == muni)
    council_slugs = [ct.value.slug for ct in CouncilTypeEnum]
    councils = sorted(
        councils, key=lambda ct: council_slugs.index(ct.council_type.value.slug)
    )

    if council_slug is not None:
        if council_slug not in council_slugs:
            raise HTTPException(status_code=404, detail="Sveitarfélag fannst ekki")
        council = db.query(Council).filter(Council.council_type == council_slug).first()
        if council is None:
            return RedirectResponse(
                request.url_for("get_municipality", muni_slug=muni.slug)
            )
    else:
        council = None

    filters = []
    if council is not None:
        filters.append(Meeting.council == council)
    else:
        filters.append(Council.municipality_id == muni.id)

    years = (
        db.query(distinct(extract("year", Meeting.start)))
        .filter(*filters)
        .order_by(extract("year", Meeting.start).desc())
    )
    years = [int(y[0]) for y in years]

    if year and year > 1900:
        filters.append(extract("year", Meeting.start) == year)

    meetings = MeetingView(db, page, *filters)

    return templates.TemplateResponse(
        "municipality.html",
        {
            "municipality": muni,
            "council": council,
            "councils": councils,
            "year": year,
            "years": years,
            "meetings": meetings,
            "paging": meetings.paging,
            "request": request,
            "user": current_user,
        },
    )


@router.get("/s/{muni_slug}/{council_slug}/fundir/{meeting_id}")
async def get_meeting(
    request: Request,
    muni_slug: str,
    council_slug: str,
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
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
            "user": current_user,
        },
    )


@router.get("/s/{muni_slug}/{council_slug}")
async def get_council(
    request: Request, muni_slug: str, council_slug: str, db: Session = Depends(get_db),
):
    return None


@router.get("/s/{muni_slug}/{council_slug}/nr/{case_id}")
async def get_case(
    request: Request,
    muni_slug: str,
    council_slug: str,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    case = db.query(Case).filter(Case.serial == case_id).first()
    if (
        case is None
        or case.council.council_type.value.slug != council_slug
        or case.council.municipality.slug != muni_slug
    ):
        raise HTTPException(status_code=404, detail="Verk fannst ekki")

    minutes = db.query(Minute).join(Meeting).filter(Minute.case_id == case.id)

    last_minute = minutes.order_by(Meeting.start.desc()).first()
    headline = last_minute.headline
    last_updated = last_minute.meeting.start

    return templates.TemplateResponse(
        "case.html",
        {
            "municipality": case.council.municipality,
            "case": case,
            "council": case.council,
            "minutes": minutes.order_by(Meeting.start),
            "request": request,
            "user": current_user,
            "headline": headline,
            "last_updated": last_updated,
        },
    )


@router.get("/s/{muni_slug}/{council_slug}/nr/{case_id}/{minute_id}")
def get_minute(
    request: Request,
    muni_slug: str,
    council_slug: str,
    case_id: str,
    minute_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    # Minutes are available on both case and meeting pages but it’s nice to have
    # permalinks for each minute as well, for links.
    minute = db.query(Minute).get(hashids.decode(minute_id)[0])
    if (
        minute is None
        or minute.case.serial != case_id
        or minute.case.council.council_type.value.slug != council_slug
        or minute.case.council.municipality.slug != muni_slug
    ):
        raise HTTPException(status_code=404, detail="Bókun fannst ekki")
    sq_count = (
        db.query(func.count(Case.id).label("case_count"))
        .filter(Case.id == minute.case_id)
        .subquery()
    )
    minute, case_count = (
        db.query(Minute, sq_count.c.case_count)
        .select_from(Minute)
        .filter(Minute.id == minute.id)
        .first()
    )

    last_updated = (
        db.query(Minute)
        .join(Meeting)
        .filter(Minute.case_id == minute.case.id)
        .order_by(Meeting.start.desc())
        .first()
    ).meeting.start

    return templates.TemplateResponse(
        "minute.html",
        {
            "municipality": minute.meeting.council.municipality,
            "council": minute.meeting.council,
            "meeting": minute.meeting,
            "minute": minute,
            "case": minute.case,
            "case_count": case_count,
            "request": request,
            "user": current_user,
            "headline": minute.headline,
            "last_updated": last_updated,
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
    request: Request,
    kennitala: str,
    slug: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    entity = _get_entity(db, kennitala, slug)
    if slug is None:
        return RedirectResponse("/f/{}-{}".format(entity.slug, entity.kennitala))
    return templates.TemplateResponse(
        "company.html", {"entity": entity, "request": request, "user": current_user}
    )


@router.get("/p/{kennitala}")
@router.get("/p/{slug}-{kennitala}")
async def get_person(
    request: Request,
    kennitala: str,
    slug: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    entity = _get_entity(db, kennitala, slug)
    if slug is None:
        return RedirectResponse("/p/{}-{}".format(entity.slug, entity.kennitala))
    return templates.TemplateResponse(
        "person.html", {"entity": entity, "request": request, "user": current_user}
    )


@router.get("/mapkit-token")
async def mapkit_token(request: Request):
    return PlainTextResponse(mapkit_get_token(config("MAPKIT_PRIVATE_KEY", cast=Secret)))
