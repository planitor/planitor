import datetime as dt
from typing import List, Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from planitor.database import get_db
from planitor.models import (
    Address,
    Case,
    CaseEntity,
    Council,
    Entity,
    Meeting,
    Minute,
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


def _case_to_dict(case: Case, council_type=None, lat=None, lon=None) -> dict:
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
    }


@router.get("/cases/nearby", response_model=PaginatedResponse[ExploreCase])
def get_nearby_cases(
    lat: float = Query(..., description="Latitude (WGS84)"),
    lon: float = Query(..., description="Longitude (WGS84)"),
    radius_m: int = Query(500, ge=1, le=5000, description="Radius in meters"),
    status: Optional[CaseStatusEnum] = None,
    council_type: Optional[CouncilTypeEnum] = None,
    updated_after: Optional[dt.date] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    geo_filter = func.earth_distance(
        func.ll_to_earth(lat, lon),
        func.ll_to_earth(Address.lat_wgs84, Address.long_wgs84),
    ) < radius_m

    # Base query: cases within radius
    query = db.query(Case).join(Address, Case.address_id == Address.hnitnum).filter(geo_filter)

    if status is not None:
        query = query.filter(Case.status == status)
    if updated_after is not None:
        query = query.filter(
            Case.updated >= dt.datetime.combine(updated_after, dt.time.min)
        )
    if council_type is not None:
        query = (
            query.join(Minute, Minute.case_id == Case.id)
            .join(Meeting, Minute.meeting_id == Meeting.id)
            .join(Council, Meeting.council_id == Council.id)
            .filter(Council.council_type == council_type)
            .distinct(Case.id)
            .order_by(Case.id)
        )
        # Wrap in subquery to re-sort
        case_ids = query.with_entities(Case.id).subquery()
        query = db.query(Case).filter(Case.id.in_(case_ids))

    total = query.count()
    cases = query.order_by(Case.updated.desc().nullslast()).offset(offset).limit(limit).all()

    items = []
    for case in cases:
        d = _case_to_dict(case)
        items.append(d)

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/minutes/search", response_model=PaginatedResponse[ExploreMinute])
def search_minutes(
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
    db: Session = Depends(get_db),
):
    if not any([q, lat and lon, entity, address, council_type, status, after, before]):
        raise HTTPException(400, "At least one filter parameter is required")

    query = (
        db.query(Minute)
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

    query = query.filter(*filters).order_by(Meeting.start.desc())

    total = query.count()
    minutes = query.offset(offset).limit(limit).all()

    items = [_minute_to_dict(m) for m in minutes]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/entities/search", response_model=List[ExploreEntity])
def search_entities(
    q: str = Query(..., min_length=1, description="Name search"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    tsquery = func.websearch_to_tsquery("simple", q)
    entities = (
        db.query(Entity)
        .filter(Entity.search_vector.op("@@")(tsquery))
        .order_by(func.ts_rank(Entity.search_vector, tsquery).desc())
        .limit(limit)
        .all()
    )
    return [{"kennitala": e.kennitala, "name": e.name} for e in entities]


@router.get(
    "/entities/{kennitala}/minutes",
    response_model=PaginatedResponse[ExploreMinute],
)
def get_entity_minutes(
    kennitala: str,
    council_type: Optional[CouncilTypeEnum] = None,
    after: Optional[dt.date] = None,
    before: Optional[dt.date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    entity = db.query(Entity).filter(Entity.kennitala == kennitala).first()
    if not entity:
        raise HTTPException(404, "Entity not found")

    query = (
        db.query(Minute)
        .join(Case, Minute.case_id == Case.id)
        .join(CaseEntity, CaseEntity.case_id == Case.id)
        .join(Meeting, Minute.meeting_id == Meeting.id)
        .join(Council, Meeting.council_id == Council.id)
        .filter(CaseEntity.entity_id == kennitala)
    )

    if council_type is not None:
        query = query.filter(Council.council_type == council_type)
    if after is not None:
        query = query.filter(Meeting.start >= dt.datetime.combine(after, dt.time.min))
    if before is not None:
        query = query.filter(Meeting.start < dt.datetime.combine(before, dt.time.min))

    query = query.order_by(Meeting.start.desc())

    total = query.count()
    minutes = query.offset(offset).limit(limit).all()

    items = [_minute_to_dict(m) for m in minutes]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/cases/{serial}", response_model=ExploreCaseDetail)
def get_case_by_serial(
    serial: str,
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.serial == serial).first()
    if not case:
        raise HTTPException(404, "Case not found")

    minutes = (
        db.query(Minute)
        .join(Meeting, Minute.meeting_id == Meeting.id)
        .filter(Minute.case_id == case.id)
        .order_by(Meeting.start.desc())
        .all()
    )

    # Get council_type from the most recent minute's meeting
    council_type = None
    if minutes:
        meeting = minutes[0].meeting
        if meeting and meeting.council:
            council_type = meeting.council.council_type

    d = _case_to_dict(case, council_type=council_type)
    d["minutes"] = [_minute_to_dict(m) for m in minutes]
    return d
