import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import distinct, extract, func
from sqlalchemy.orm import Session
from starlette.requests import Request

from planitor import hashids
from planitor import crud
from planitor.database import get_db
from planitor.meetings import MeetingView
from planitor.models import (
    Address,
    Case,
    CaseEntity,
    Council,
    CouncilTypeEnum,
    Meeting,
    Minute,
    Municipality,
    User,
)
from planitor.search import MinuteResults
from planitor.security import get_current_active_user_or_none
from planitor.templates import templates

from .utils import _get_entity

router = APIRouter()


@router.get("/leit")
async def get_search(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
    q: str = "",
    page: int = 1,
):
    if q:
        results = MinuteResults(db, q, page)
    else:
        results = None

    iceaddr_matches = crud.search_addresses(q)
    entity_matches = crud.search_entities(db, q)

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "q": q,
            "user": current_user,
            "results": results,
            "iceaddr_matches": iceaddr_matches,
            "entity_matches": entity_matches,
        },
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

    status_counts = (
        db.query(Minute.status, func.count(Minute.status))
        .group_by(Minute.status, Minute.meeting_id)
        .having(Minute.meeting_id == meeting.id)
    )

    sq_count = (
        db.query(Case.id, func.count(Minute.id).label("minute_count"))
        .join(Minute, Case.id == Minute.case_id)
        .group_by(Case.id)
        .subquery()
    )

    minutes = (
        db.query(Minute, sq_count.c.minute_count)
        .select_from(Minute)
        .filter(Minute.meeting_id == meeting.id)
        .join(sq_count, sq_count.c.id == Minute.case_id)
        .order_by(Minute.id)
    )

    return templates.TemplateResponse(
        "meeting.html",
        {
            "municipality": meeting.council.municipality,
            "status_counts": status_counts,
            "council": meeting.council,
            "meeting": meeting,
            "minutes": minutes,
            "request": request,
            "user": current_user,
        },
    )


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

    minutes = (
        db.query(Minute)
        .join(Meeting)
        .filter(Minute.case_id == case.id)
        .order_by(Meeting.start.desc())
    )

    last_minute = minutes.first()
    last_updated = last_minute.meeting.start

    if case.iceaddr is not None:
        related_cases = (
            db.query(Case)
            .filter(Case.iceaddr == case.iceaddr)
            .filter(Case.id != case.id)
            .order_by(Case.updated.desc())
        )
    else:
        related_cases = []

    subscription = crud.get_case_subscription(db, current_user, case)

    address_subscription = crud.get_address_subscription(db, current_user, case.iceaddr)

    return templates.TemplateResponse(
        "case.html",
        {
            "municipality": case.council.municipality,
            "case": case,
            "council": case.council,
            "minutes": minutes,
            "request": request,
            "user": current_user,
            "last_updated": last_updated,
            "related_cases": related_cases,
            "subscription": subscription,
            "address_subscription": address_subscription,
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

    next_minute = (
        db.query(Minute)
        .filter(Minute.meeting == minute.meeting, Minute.id > minute.id)
        .order_by(Minute.id)
        .first()
    )

    previous_minute = (
        db.query(Minute)
        .filter(Minute.meeting == minute.meeting, Minute.id < minute.id)
        .order_by(Minute.id.desc())
        .first()
    )

    subscription = crud.get_case_subscription(db, current_user, minute.case)

    case = minute.case
    if case.iceaddr is not None:
        related_cases = (
            db.query(Case)
            .filter(Case.iceaddr == case.iceaddr)
            .filter(Case.id != case.id)
            .order_by(Case.updated.desc())
        )
    else:
        related_cases = []

    address_subscription = crud.get_address_subscription(db, current_user, case.iceaddr)

    return templates.TemplateResponse(
        "minute.html",
        {
            "municipality": minute.meeting.council.municipality,
            "council": minute.meeting.council,
            "meeting": minute.meeting,
            "minute": minute,
            "case": case,
            "case_count": case_count,
            "request": request,
            "user": current_user,
            "headline": minute.headline,
            "last_updated": last_updated,
            "next_minute": next_minute,
            "previous_minute": previous_minute,
            "subscription": subscription,
            "related_cases": related_cases,
            "address_subscription": address_subscription,
        },
    )


@router.get("/heimilisfong/{hnitnum}")
async def get_address(
    request: Request,
    hnitnum: int,
    db: Session = Depends(get_db),
    radius: int = 300,
    days: int = 365,
    current_user: User = Depends(get_current_active_user_or_none),
):

    address = crud.get_and_init_address(hnitnum)
    if not address:
        raise HTTPException(404)

    _db_address = db.query(Address).filter(Address.hnitnum == hnitnum).first()

    if _db_address is not None:
        address = _db_address

    if current_user is None:
        return templates.TemplateResponse(
            "address_paywall.html", {"request": request, "address": address}
        )

    def get_query(filters):
        sq = (
            db.query(Case.id, func.count(Minute.id).label("minute_count"))
            .join(Address)
            .join(Minute, Case.id == Minute.case_id)
            .filter(*filters)
            .group_by(Case.id)
            .subquery()
        )

        return (
            db.query(
                Case,
                extract("year", Case.updated),
                sq.c.minute_count,
            )
            .select_from(Case)
            .outerjoin(Address)
            .filter(*filters)
            .join(sq, sq.c.id == Case.id)
            .order_by(Case.updated.desc())
        )

    cases = get_query((Address.hnitnum == hnitnum,))

    if days < 1:
        days = 1
    if days > 365:
        days = 365

    if radius < 1:
        radius = 1
    if radius > 1000:
        radius = 1000

    dt_days_ago = dt.datetime.utcnow() - dt.timedelta(days=days)

    nearby_cases = get_query(
        (
            func.earth_distance(
                func.ll_to_earth(address.lat_wgs84, address.long_wgs84),
                func.ll_to_earth(Address.lat_wgs84, Address.long_wgs84),
            )
            < radius,
            Case.updated > dt_days_ago,
            Address.hnitnum != hnitnum,
        )
    )

    subscription = crud.get_address_subscription(db, current_user, address)

    return templates.TemplateResponse(
        "address.html",
        {
            "address": address,
            "cases": cases.all(),
            "nearby_cases": nearby_cases.limit(100).all(),
            "request": request,
            "user": current_user,
            "radius": radius,
            "days": days,
            "subscription": subscription,
        },
    )


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

    if current_user is None:
        return templates.TemplateResponse(
            "company_paywall.html", {"request": request, "entity": entity}
        )

    sq_count = (
        db.query(Case.id, func.count(Minute.id).label("minute_count"))
        .join(CaseEntity)
        .filter(CaseEntity.entity == entity)
        .join(Minute, Case.id == Minute.case_id)
        .group_by(Case.id)
        .subquery()
    )

    cases = (
        db.query(
            Case,
            extract("year", Case.updated),
            sq_count.c.minute_count,
        )
        .select_from(Case)
        .join(CaseEntity)
        .filter(CaseEntity.entity == entity)
        .join(sq_count, sq_count.c.id == Case.id)
        .order_by(Case.updated.desc())
    )

    subscription = crud.get_entity_subscription(db, current_user, entity)

    return templates.TemplateResponse(
        "company.html",
        {
            "entity": entity,
            "cases": cases,
            "request": request,
            "user": current_user,
            "subscription": subscription,
        },
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
    return await get_company(request, kennitala, slug, db, current_user)


@router.get("/minutes/{id}")
def get_minute_by_id(
    request: Request,
    id: str,
    db: Session = Depends(get_db),
):
    minute = db.query(Minute).get(id)
    if minute is None:
        raise HTTPException(404)
    council = minute.meeting.council
    return RedirectResponse(
        request.url_for(
            "get_minute",
            muni_slug=council.municipality.slug,
            council_slug=council.council_type.value.slug,
            case_id=minute.case.serial,
            minute_id=hashids.encode(minute.id),
        )
    )


@router.get("/meetings/{id}")
def get_meetings_by_id(
    request: Request,
    id: str,
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).get(id)
    if meeting is None:
        raise HTTPException(404)
    council = meeting.council
    return RedirectResponse(
        request.url_for(
            "get_meeting",
            muni_slug=council.municipality.slug,
            council_slug=council.council_type.value.slug,
            meeting_id=hashids.encode(meeting.id),
        )
    )


@router.get("/cases/{id}")
def get_case_by_id(
    request: Request,
    id: str,
    db: Session = Depends(get_db),
):
    case = db.query(Case).get(id)
    if case is None:
        raise HTTPException(404)
    council = case.council
    return RedirectResponse(
        request.url_for(
            "get_case",
            muni_slug=council.municipality.slug,
            council_slug=council.council_type.value.slug,
            case_id=case.serial,
        )
    )
