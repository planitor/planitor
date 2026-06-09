import datetime as dt
from typing import List, Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from planitor.database import get_async_db
from planitor.models import (
    Address,
    Case,
    CaseEntity,
    Council,
    Entity,
    Meeting,
    Minute,
    PropertyTransaction,
)
from planitor.models.enums import CaseStatusEnum, CouncilTypeEnum
from planitor.schemas.city import (
    ExploreCase,
    ExploreCaseDetail,
    ExploreEntity,
    ExploreMinute,
    PaginatedResponse,
)
from planitor.search import get_tsquery

from . import router


def _minute_to_dict(minute: Minute) -> dict:
    meeting = minute.meeting
    case = minute.case
    return {
        "id": minute.id,
        "headline": minute.headline,
        "inquiry": minute.inquiry,
        "remarks": minute.remarks,
        "status": minute.status,
        "meeting_date": meeting.start.date() if meeting else None,
        "council": meeting.council_name if meeting else None,
        "case_serial": case.serial if case else None,
        "case_address": case.address if case else None,
    }


def _case_to_dict(
    case: Case, council_type=None, lat=None, lon=None, last_sale=None
) -> dict:
    if case.iceaddr:
        lat = float(case.iceaddr.lat_wgs84) if case.iceaddr.lat_wgs84 else None
        lon = float(case.iceaddr.long_wgs84) if case.iceaddr.long_wgs84 else None
    return {
        "id": case.id,
        "serial": case.serial,
        "address": case.address,
        "status": case.status,
        "updated": case.updated,
        "lat": lat,
        "lon": lon,
        "council_type": council_type,
        "last_sale_price": (
            int(last_sale.kaupverd) if last_sale and last_sale.kaupverd else None
        ),
        "last_sale_date": last_sale.utgefid if last_sale else None,
    }


MINUTE_LOAD_OPTIONS = (
    selectinload(Minute.meeting).selectinload(Meeting.council),
    selectinload(Minute.case),
)

CASE_LOAD_OPTIONS = (selectinload(Case.iceaddr),)


async def _get_latest_sales(db: AsyncSession, address_ids: list) -> dict:
    """Batch-fetch the most recent PropertyTransaction per address_id."""
    if not address_ids:
        return {}
    latest_sq = (
        select(
            PropertyTransaction.address_id,
            func.max(PropertyTransaction.utgefid).label("max_date"),
        )
        .where(PropertyTransaction.address_id.in_(address_ids))
        .group_by(PropertyTransaction.address_id)
        .subquery()
    )
    rows = await db.scalars(
        select(PropertyTransaction).join(
            latest_sq,
            and_(
                PropertyTransaction.address_id == latest_sq.c.address_id,
                PropertyTransaction.utgefid == latest_sq.c.max_date,
            ),
        )
    )
    # Keep one per address_id (highest kaupverd if ties)
    result = {}
    for tx in rows.all():
        prev = result.get(tx.address_id)
        if prev is None or (tx.kaupverd or 0) > (prev.kaupverd or 0):
            result[tx.address_id] = tx
    return result


@router.get("/cases/nearby", response_model=PaginatedResponse[ExploreCase])
async def get_nearby_cases(
    lat: float = Query(..., description="Latitude (WGS84)"),
    lon: float = Query(..., description="Longitude (WGS84)"),
    radius_m: int = Query(500, ge=1, le=5000, description="Radius in meters"),
    status: Optional[CaseStatusEnum] = None,
    council_type: Optional[CouncilTypeEnum] = None,
    updated_after: Optional[dt.date] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
):
    geo_filter = (
        func.earth_distance(
            func.ll_to_earth(lat, lon),
            func.ll_to_earth(Address.lat_wgs84, Address.long_wgs84),
        )
        < radius_m
    )

    # Base query: cases within radius
    query = (
        select(Case)
        .options(*CASE_LOAD_OPTIONS)
        .join(Address, Case.address_id == Address.hnitnum)
        .where(geo_filter)
    )

    if status is not None:
        query = query.where(Case.status == status)
    if updated_after is not None:
        query = query.where(
            Case.updated >= dt.datetime.combine(updated_after, dt.time.min)
        )
    if council_type is not None:
        query = (
            query.join(Minute, Minute.case_id == Case.id)
            .join(Meeting, Minute.meeting_id == Meeting.id)
            .join(Council, Meeting.council_id == Council.id)
            .where(Council.council_type == council_type)
            .distinct(Case.id)
            .order_by(Case.id)
        )
        # Wrap in subquery to re-sort
        case_ids = select(query.subquery().c.id)
        query = select(Case).options(*CASE_LOAD_OPTIONS).where(Case.id.in_(case_ids))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    cases = (
        await db.scalars(
            query.order_by(Case.updated.desc().nullslast()).offset(offset).limit(limit)
        )
    ).all()

    sales = await _get_latest_sales(db, [c.address_id for c in cases if c.address_id])
    items = [_case_to_dict(c, last_sale=sales.get(c.address_id)) for c in cases]

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/minutes/search", response_model=PaginatedResponse[ExploreMinute])
async def search_minutes(
    q: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_m: int = Query(500, ge=1, le=5000),
    entity: Optional[str] = Query(None, description="Kennitala to filter by entity"),
    address: Optional[str] = Query(None, description="ILIKE filter on case address"),
    council_type: Optional[CouncilTypeEnum] = None,
    status: Optional[CaseStatusEnum] = None,
    after: Optional[dt.date] = None,
    before: Optional[dt.date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
):
    if not any([q, lat and lon, entity, address, council_type, status, after, before]):
        raise HTTPException(400, "At least one filter parameter is required")

    query = (
        select(Minute)
        .options(*MINUTE_LOAD_OPTIONS)
        .join(Meeting, Minute.meeting_id == Meeting.id)
        .join(Council, Meeting.council_id == Council.id)
        .outerjoin(Case, Minute.case_id == Case.id)
    )

    filters = []

    if q:
        tsquery = get_tsquery(q)
        filters.append(Minute.search_vector.op("@@")(tsquery))

    if lat is not None and lon is not None:
        query = query.join(Address, Case.address_id == Address.hnitnum)
        filters.append(
            func.earth_distance(
                func.ll_to_earth(lat, lon),
                func.ll_to_earth(Address.lat_wgs84, Address.long_wgs84),
            )
            < radius_m
        )

    if entity:
        query = query.join(CaseEntity, CaseEntity.case_id == Case.id)
        filters.append(CaseEntity.entity_id == entity)

    if address:
        filters.append(Case.address.ilike(f"%{address}%"))

    if council_type is not None:
        filters.append(Council.council_type == council_type)

    if status is not None:
        filters.append(Minute.status == status)

    if after is not None:
        filters.append(Meeting.start >= dt.datetime.combine(after, dt.time.min))

    if before is not None:
        filters.append(Meeting.start < dt.datetime.combine(before, dt.time.min))

    query = query.where(*filters).order_by(Meeting.start.desc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    minutes = (await db.scalars(query.offset(offset).limit(limit))).all()

    items = [_minute_to_dict(m) for m in minutes]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/entities/search", response_model=List[ExploreEntity])
async def search_entities(
    q: str = Query(..., min_length=1, description="Name search"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    tsquery = func.websearch_to_tsquery("simple", q)
    entities = await db.scalars(
        select(Entity)
        .where(Entity.search_vector.op("@@")(tsquery))
        .order_by(func.ts_rank(Entity.search_vector, tsquery).desc())
        .limit(limit)
    )
    return [{"kennitala": e.kennitala, "name": e.name} for e in entities.all()]


@router.get(
    "/entities/{kennitala}/minutes",
    response_model=PaginatedResponse[ExploreMinute],
)
async def get_entity_minutes(
    kennitala: str,
    council_type: Optional[CouncilTypeEnum] = None,
    after: Optional[dt.date] = None,
    before: Optional[dt.date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
):
    entity = await db.scalar(select(Entity).where(Entity.kennitala == kennitala))
    if not entity:
        raise HTTPException(404, "Entity not found")

    query = (
        select(Minute)
        .options(*MINUTE_LOAD_OPTIONS)
        .join(Case, Minute.case_id == Case.id)
        .join(CaseEntity, CaseEntity.case_id == Case.id)
        .join(Meeting, Minute.meeting_id == Meeting.id)
        .join(Council, Meeting.council_id == Council.id)
        .where(CaseEntity.entity_id == kennitala)
    )

    if council_type is not None:
        query = query.where(Council.council_type == council_type)
    if after is not None:
        query = query.where(Meeting.start >= dt.datetime.combine(after, dt.time.min))
    if before is not None:
        query = query.where(Meeting.start < dt.datetime.combine(before, dt.time.min))

    query = query.order_by(Meeting.start.desc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    minutes = (await db.scalars(query.offset(offset).limit(limit))).all()

    items = [_minute_to_dict(m) for m in minutes]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/cases/{serial}", response_model=ExploreCaseDetail)
async def get_case_by_serial(
    serial: str,
    db: AsyncSession = Depends(get_async_db),
):
    case = await db.scalar(
        select(Case).options(*CASE_LOAD_OPTIONS).where(Case.serial == serial)
    )
    if not case:
        raise HTTPException(404, "Case not found")

    minutes = (
        await db.scalars(
            select(Minute)
            .options(*MINUTE_LOAD_OPTIONS)
            .join(Meeting, Minute.meeting_id == Meeting.id)
            .where(Minute.case_id == case.id)
            .order_by(Meeting.start.desc())
        )
    ).all()

    # Get council_type from the most recent minute's meeting
    council_type = None
    if minutes:
        meeting = minutes[0].meeting
        if meeting and meeting.council:
            council_type = meeting.council.council_type

    # Property transactions at this address
    transactions = []
    last_sale = None
    if case.address_id:
        transactions = (
            await db.scalars(
                select(PropertyTransaction)
                .where(PropertyTransaction.address_id == case.address_id)
                .order_by(PropertyTransaction.utgefid.desc().nullslast())
            )
        ).all()
        if transactions:
            last_sale = transactions[0]

    d = _case_to_dict(case, council_type=council_type, last_sale=last_sale)
    d["minutes"] = [_minute_to_dict(m) for m in minutes]
    d["transactions"] = [
        {
            "fastnum": t.fastnum,
            "kaupverd": int(t.kaupverd) if t.kaupverd else None,
            "utgefid": t.utgefid,
            "tegund": t.tegund,
            "flatarmal": float(t.flatarmal) if t.flatarmal else None,
            "fjoldi_herbergja": (
                float(t.fjoldi_herbergja) if t.fjoldi_herbergja else None
            ),
            "byggingarar": t.byggingarar,
        }
        for t in transactions
    ]
    return d
