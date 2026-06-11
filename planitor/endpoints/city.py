import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import distinct, extract, func, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
from starlette.requests import Request
import skipulagsstofnun

from planitor import crud, hashids
from planitor.database import get_async_db, get_db
from planitor.permits import PermitMinuteView
from planitor.meetings import MeetingView
from planitor.models import (
    Address,
    Case,
    CaseEntity,
    CaseStatusEnum,
    Council,
    CouncilTypeEnum,
    DeiliskipulagPlan,
    Entity,
    EntityTypeEnum,
    Meeting,
    Minute,
    Municipality,
    PropertyTransaction,
    User,
)
from planitor.search import MinuteResults, Pagination
from planitor.security import get_current_active_user_or_none
from planitor.templates import templates

from .utils import _get_entity

router = APIRouter()


def _get_deiliskipulag(db, lat, lon):
    """Look up deiliskipulag for coordinates. Returns (plan_data, db_plan)."""
    polygon, plan_data = skipulagsstofnun.plans.get_plan(lat, lon)
    if plan_data is None:
        return None, None
    skipnr = int(plan_data["skipnr"])
    db_plan = db.query(DeiliskipulagPlan).get(skipnr)
    return plan_data, db_plan


@router.get("/leit")
def get_search(
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
async def get_index(
    request: Request,
    current_user: User = Depends(get_current_active_user_or_none),
    db: AsyncSession = Depends(get_async_db),
):
    sixty_days_ago = dt.datetime.utcnow() - dt.timedelta(days=60)

    # Latest meeting per council (existing)
    sq = (
        select(Meeting.council_id, func.max(Meeting.start).label("meeting_latest"))
        .group_by(Meeting.council_id)
        .subquery()
    )
    meetings = (
        await db.scalars(
            select(Meeting)
            .options(selectinload(Meeting.council).selectinload(Council.municipality))
            .join(
                sq,
                and_(
                    sq.c.council_id == Meeting.council_id,
                    sq.c.meeting_latest == Meeting.start,
                ),
            )
            .order_by(Meeting.start.desc())
        )
    ).all()

    # Quick stats
    total_meetings = await db.scalar(
        select(func.count(Meeting.id)).where(Meeting.start >= sixty_days_ago)
    )
    total_minutes = await db.scalar(
        select(func.count(Minute.id))
        .join(Meeting)
        .where(Meeting.start >= sixty_days_ago)
    )
    total_new_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.created >= sixty_days_ago)
    )

    # Hot addresses: top 10 addresses with most minute entries in last 60 days
    hot_addresses = (
        await db.execute(
            select(
                Address,
                func.count(Minute.id).label("minute_count"),
            )
            .join(Case, Case.address_id == Address.hnitnum)
            .join(Minute, Minute.case_id == Case.id)
            .join(Meeting, Minute.meeting_id == Meeting.id)
            .where(Meeting.start >= sixty_days_ago, Case.address_id.isnot(None))
            .group_by(Address.hnitnum)
            .order_by(func.count(Minute.id).desc())
            .limit(10)
        )
    ).all()

    # Latest case headline per hot address
    hot_address_hnits = [a.hnitnum for a, _ in hot_addresses]
    hot_address_headlines = {}
    if hot_address_hnits:
        for hnitnum in hot_address_hnits:
            latest_case = await db.scalar(
                select(Case)
                .where(Case.address_id == hnitnum)
                .order_by(Case.updated.desc())
                .limit(1)
            )
            if latest_case and latest_case.headline:
                hot_address_headlines[hnitnum] = latest_case.headline

    # Hottest streets: top 5 streets by distinct case count
    hot_streets = (
        await db.execute(
            select(
                Address.heiti_nf,
                func.count(distinct(Case.id)).label("case_count"),
            )
            .join(Case, Case.address_id == Address.hnitnum)
            .join(Minute, Minute.case_id == Case.id)
            .join(Meeting, Minute.meeting_id == Meeting.id)
            .where(Meeting.start >= sixty_days_ago, Address.heiti_nf.isnot(None))
            .group_by(Address.heiti_nf)
            .order_by(func.count(distinct(Case.id)).desc())
            .limit(5)
        )
    ).all()

    # Status scoreboard: count of each status in last 60 days
    status_counts = (
        await db.execute(
            select(
                Minute.status,
                func.count(Minute.id).label("count"),
            )
            .join(Meeting)
            .where(Meeting.start >= sixty_days_ago, Minute.status.isnot(None))
            .group_by(Minute.status)
            .order_by(func.count(Minute.id).desc())
        )
    ).all()

    # Busiest entities: top 5 companies by distinct case count
    busy_entities = (
        await db.execute(
            select(
                Entity,
                func.count(distinct(Case.id)).label("case_count"),
            )
            .join(CaseEntity, CaseEntity.entity_id == Entity.kennitala)
            .join(Case, CaseEntity.case_id == Case.id)
            .join(Minute, Minute.case_id == Case.id)
            .join(Meeting, Minute.meeting_id == Meeting.id)
            .where(
                Meeting.start >= sixty_days_ago,
                Entity.entity_type == EntityTypeEnum.company,
            )
            .group_by(Entity.kennitala)
            .order_by(func.count(distinct(Case.id)).desc())
            .limit(5)
        )
    ).all()

    # Freshest cases: 5 most recently created
    fresh_cases = (
        await db.scalars(
            select(Case)
            .options(selectinload(Case.municipality), selectinload(Case.iceaddr))
            .where(Case.created >= sixty_days_ago)
            .order_by(Case.created.desc())
            .limit(5)
        )
    ).all()

    # Map pins: distinct addresses with recent activity and coordinates
    ninety_days_ago = dt.datetime.utcnow() - dt.timedelta(days=90)
    # Capital area bounding box (approximate)
    LAT_MIN, LAT_MAX = 64.05, 64.20
    LON_MIN, LON_MAX = -22.05, -21.70

    map_pin_rows = (
        await db.execute(
            select(
                Address.hnitnum,
                Address.lat_wgs84,
                Address.long_wgs84,
                func.max(Case.id).label("latest_case_id"),
            )
            .join(Case, Case.address_id == Address.hnitnum)
            .join(Minute, Minute.case_id == Case.id)
            .join(Meeting, Minute.meeting_id == Meeting.id)
            .where(
                Meeting.start >= ninety_days_ago,
                Address.lat_wgs84.isnot(None),
                Address.long_wgs84.isnot(None),
                Address.lat_wgs84.between(LAT_MIN, LAT_MAX),
                Address.long_wgs84.between(LON_MIN, LON_MAX),
            )
            .group_by(Address.hnitnum, Address.lat_wgs84, Address.long_wgs84)
            .limit(150)
        )
    ).all()

    map_pins = []
    if map_pin_rows:
        case_ids = [row.latest_case_id for row in map_pin_rows]
        cases_by_id = {
            c.id: c
            for c in (
                await db.scalars(
                    select(Case)
                    .options(selectinload(Case.iceaddr))
                    .where(Case.id.in_(case_ids))
                )
            ).all()
        }
        for row in map_pin_rows:
            case = cases_by_id.get(row.latest_case_id)
            if not case:
                continue
            address = case.iceaddr
            if not address:
                continue
            status_color = case.status.value.color if case.status else None
            map_pins.append(
                {
                    "lat": float(row.lat_wgs84),
                    "lon": float(row.long_wgs84),
                    "label": address.address or "",
                    "status_color": status_color,
                    "headline": case.headline or "",
                    "url": f"/heimilisfong/{row.hnitnum}",
                }
            )

    # Themed case clusters — search index queries, no time window
    theme_clusters = [
        ("Kærur", "kæra"),
        ("Skipulagsbreytingar", "deiliskipulag & breyting"),
        ("Niðurrif", "niðurrif | rífa"),
        ("Hótel og gisting", "hótel | gistirými | gistiheimili"),
        ("Starfsleyfi", "starfsleyfi"),
    ]
    themed_cases = []
    for label, query_str in theme_clusters:
        tsquery = func.to_tsquery("simple", query_str)
        case_ids_sq = (
            select(Case.id)
            .join(Minute, Minute.case_id == Case.id)
            .where(Minute.search_vector.op("@@")(tsquery))
            .group_by(Case.id)
            .order_by(func.max(Case.updated).desc().nullslast())
            .limit(5)
            .subquery()
        )
        cases = (
            await db.scalars(
                select(Case)
                .options(selectinload(Case.municipality), selectinload(Case.iceaddr))
                .where(Case.id.in_(select(case_ids_sq.c.id)))
                .order_by(Case.updated.desc().nullslast())
            )
        ).all()
        if cases:
            themed_cases.append((label, cases))

    return templates.TemplateResponse(
        "municipalities.html",
        {
            "request": request,
            "user": current_user,
            "meetings": meetings,
            "total_meetings": total_meetings,
            "total_minutes": total_minutes,
            "total_new_cases": total_new_cases,
            "hot_addresses": hot_addresses,
            "hot_address_headlines": hot_address_headlines,
            "hot_streets": hot_streets,
            "status_counts": status_counts,
            "busy_entities": busy_entities,
            "fresh_cases": fresh_cases,
            "themed_cases": themed_cases,
            "map_pins": map_pins,
        },
    )


@router.get("/s/{muni_slug}")
@router.get("/s/{muni_slug}/{council_slug}")
def get_municipality(
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
    council_slugs = [str(ct) for ct in CouncilTypeEnum]
    councils = sorted(
        councils, key=lambda ct: council_slugs.index(str(ct.council_type))
    )

    if council_slug is not None:
        if council_slug not in council_slugs:
            raise HTTPException(status_code=404, detail="Sveitarfélag fannst ekki")
        council = (
            db.query(Council)
            .filter(Council.council_type == council_slug, Council.municipality == muni)
            .first()
        )
        if council is None:
            return RedirectResponse(
                request.url_for("get_municipality", muni_slug=muni.slug)
            )
    else:
        council = None

    filters = []

    filters.append(Council.municipality_id == muni.id)

    if council is not None:
        filters.append(Meeting.council == council)

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
def get_meeting(
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
        or meeting.council.council_type.value != council_slug
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
def get_case_legacy_redirect(
    request: Request,
    muni_slug: str,
    council_slug: str,
    case_id: str,
):
    return RedirectResponse(f"/s/{muni_slug}/nr/{case_id}")


@router.get("/s/{muni_slug}/nr/{case_id}")
def get_case(
    request: Request,
    muni_slug: str,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    case = db.query(Case).filter(Case.serial == case_id).first()
    if case is None or case.municipality.slug != muni_slug:
        raise HTTPException(status_code=404, detail="Verk fannst ekki")

    minutes = (
        db.query(Minute)
        .join(Meeting)
        .filter(Minute.case_id == case.id)
        .order_by(Meeting.start.desc())
    )

    last_minute = minutes.first()
    last_updated = last_minute.meeting.start
    council = last_minute.meeting.council if last_minute else None

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

    property_transactions = []
    if case.address_id:
        property_transactions = (
            db.query(PropertyTransaction)
            .filter(PropertyTransaction.address_id == case.address_id)
            .order_by(PropertyTransaction.utgefid.desc().nullslast())
            .all()
        )

    plan_data, db_plan = None, None
    coords = case.get_coordinates()
    if coords:
        plan_data, db_plan = _get_deiliskipulag(db, coords[0], coords[1])

    return templates.TemplateResponse(
        "case.html",
        {
            "municipality": case.municipality,
            "council": council,
            "case": case,
            "minutes": minutes,
            "request": request,
            "user": current_user,
            "last_updated": last_updated,
            "related_cases": related_cases,
            "subscription": subscription,
            "address_subscription": address_subscription,
            "property_transactions": property_transactions,
            "plan_data": plan_data,
            "db_plan": db_plan,
        },
    )


@router.get("/s/{muni_slug}/{council_slug}/nr/{case_id}/{minute_id}")
def get_minute_legacy_redirect(
    request: Request,
    muni_slug: str,
    council_slug: str,
    case_id: str,
    minute_id: str,
):
    return RedirectResponse(f"/s/{muni_slug}/nr/{case_id}/{minute_id}")


@router.get("/s/{muni_slug}/nr/{case_id}/{minute_id}")
def get_minute(
    request: Request,
    muni_slug: str,
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
        or minute.case.municipality.slug != muni_slug
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

    case_minutes = (
        db.query(Minute)
        .join(Meeting)
        .filter(Minute.case_id == case.id)
        .order_by(Meeting.start.desc())
    )

    property_transactions = []
    if case.address_id:
        property_transactions = (
            db.query(PropertyTransaction)
            .filter(PropertyTransaction.address_id == case.address_id)
            .order_by(PropertyTransaction.utgefid.desc().nullslast())
            .all()
        )

    plan_data, db_plan = None, None
    coords = case.get_coordinates()
    if coords:
        plan_data, db_plan = _get_deiliskipulag(db, coords[0], coords[1])

    return templates.TemplateResponse(
        "minute.html",
        {
            "municipality": minute.meeting.council.municipality,
            "council": minute.meeting.council,
            "meeting": minute.meeting,
            "minute": minute,
            "case": case,
            "case_count": case_count,
            "case_minutes": case_minutes,
            "request": request,
            "user": current_user,
            "headline": minute.headline,
            "last_updated": last_updated,
            "next_minute": next_minute,
            "previous_minute": previous_minute,
            "subscription": subscription,
            "related_cases": related_cases,
            "address_subscription": address_subscription,
            "property_transactions": property_transactions,
            "plan_data": plan_data,
            "db_plan": db_plan,
        },
    )


@router.get("/heimilisfong/{hnitnum}")
def get_address(
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

    municipality = (
        db.query(Municipality).filter(Municipality.id == address.svfnr).first()
    )

    polygon, plan = None, None
    plan_data, db_plan = None, None
    if address:
        polygon, plan = skipulagsstofnun.plans.get_plan(
            address.lat_wgs84, address.long_wgs84
        )
        if plan:
            plan_data, db_plan = _get_deiliskipulag(
                db, address.lat_wgs84, address.long_wgs84
            )

    property_transactions = (
        db.query(PropertyTransaction)
        .filter(PropertyTransaction.address_id == hnitnum)
        .order_by(PropertyTransaction.utgefid.desc().nullslast())
        .all()
    )

    return templates.TemplateResponse(
        "address.html",
        {
            "address": address,
            "municipality": municipality,
            "cases": cases.all(),
            "nearby_cases": nearby_cases.limit(100).all(),
            "request": request,
            "user": current_user,
            "radius": radius,
            "days": days,
            "subscription": subscription,
            "polygon": polygon,
            "plan": plan,
            "plan_data": plan_data,
            "db_plan": db_plan,
            "property_transactions": property_transactions,
        },
    )


@router.get("/f/{kennitala}")
@router.get("/f/{slug}-{kennitala}")
def get_company(
    request: Request,
    kennitala: str,
    slug: str = None,
    q: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    entity = _get_entity(db, kennitala, slug)

    if slug is None:
        return RedirectResponse("/f/{}-{}".format(entity.slug, entity.kennitala))

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
    )

    if q:
        tsquery = func.websearch_to_tsquery("simple", q)
        cases = (
            cases.join(Minute, Case.id == Minute.case_id)
            .filter(Minute.search_vector.op("@@")(tsquery))
            .distinct()
        )

    cases = cases.order_by(Case.updated.desc())

    count_query = db.query(func.count()).select_from(cases.subquery())
    pagination = Pagination(cases, count_query, page)

    subscription = None
    if current_user:
        subscription = crud.get_entity_subscription(db, current_user, entity)

    return templates.TemplateResponse(
        "company.html",
        {
            "entity": entity,
            "cases": pagination.query,
            "pagination": pagination,
            "q": q,
            "request": request,
            "user": current_user,
            "subscription": subscription,
        },
    )


@router.get("/p/{kennitala}")
@router.get("/p/{slug}-{kennitala}")
def get_person(
    request: Request,
    kennitala: str,
    slug: str = None,
    q: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_none),
):
    return get_company(request, kennitala, slug, q, page, db, current_user)


@router.get("/minutes/{id}")
def get_minute_by_id(
    request: Request,
    id: int,
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
            case_id=minute.case.serial,
            minute_id=hashids.encode(minute.id),
        )
    )


@router.get("/minutes/{id}/suggested_plan")
def get_permit_minute(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
):
    """Guess attributes of a permit from a meeting note."""
    minute = db.query(Minute).get(id)
    if minute is None:
        raise HTTPException(404)
    area = None
    units = None
    permit_type = None
    building_type = None
    return {
        "area": area,
        "units": units,
        "permit_type": permit_type,
        "building_type": building_type,
    }


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
            council_slug=council.council_type.value,
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
    return RedirectResponse(
        request.url_for(
            "get_case",
            muni_slug=case.municipality.slug,
            case_id=case.serial,
        )
    )


@router.get("/permits/minutes")
def get_permit_minutes(
    request: Request,
    db: Session = Depends(get_db),
    per_page: int = 100,
    page: str = "",
):
    permit_minutes = PermitMinuteView(db, page_bookmark=page)
    return templates.TemplateResponse(
        "minute_permits.html",
        {
            "request": request,
            "permit_minutes": permit_minutes,
            "paging": permit_minutes.page.paging,
        },
    )
