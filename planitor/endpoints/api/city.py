import datetime as dt
from typing import List

from fastapi import Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
import skipulagsstofnun

from planitor.crud.city import get_and_init_address
from planitor.database import get_db
from planitor.models import (
    Address,
    Case,
    CaseEntity,
    Council,
    Municipality,
)
from planitor.schemas import city as schemas

from ..utils import _get_entity
from . import router


@router.get("/municipalities", response_model=List[schemas.Municipality])
def get_municipalities(
    request: Request,
    db: Session = Depends(get_db),
):
    return db.query(Municipality).outerjoin(Council).all()


@router.get("/addresses/{hnitnum}/addresses", response_model=schemas.MapCasesResponse)
async def get_nearby_case_addresses(
    request: Request,
    hnitnum: int,
    radius: int = 500,
    days: int = 30,
    db: Session = Depends(get_db),
):
    address = get_and_init_address(hnitnum)
    if not address:
        raise HTTPException(404)

    _db_address = db.query(Address).filter(Address.hnitnum == hnitnum).first()

    if _db_address is not None:
        address = _db_address

    if days < 1:
        days = 1
    if days > 365:
        days = 365

    if radius < 1:
        radius = 1
    if radius > 500:
        radius = 500

    dt_days_ago = dt.datetime.utcnow() - dt.timedelta(days=days)

    filters = (
        func.earth_distance(
            func.ll_to_earth(address.lat_wgs84, address.long_wgs84),
            func.ll_to_earth(Address.lat_wgs84, Address.long_wgs84),
        )
        < radius,
        Case.updated > dt_days_ago,
    )

    most_recent_nearby_addresses = (
        db.query(Case.address_id, Case.id, Case.status, Case.updated)
        .join(Address)
        .distinct(Case.address_id)
        .filter(*filters)
        .order_by(Case.address_id, Case.updated.desc())
    )
    sq = most_recent_nearby_addresses.subquery()

    query = (
        db.query(Address, sq.c.status)
        .select_from(Address)
        .join(sq, sq.c.address_id == Address.hnitnum)
        .order_by(sq.c.updated.desc())
    )

    polygon, plan = skipulagsstofnun.plans.get_plan(
        address.lat_wgs84, address.long_wgs84
    )
    if polygon is not None:
        polygon = list(polygon.exterior.coords)

    return {
        "plan": {"plan": plan, "polygon": polygon} if plan is not None else None,
        "address": dict(
            lat=address.lat_wgs84,
            lon=address.long_wgs84,
            label=str(address),
        ),
        "addresses": [
            dict(
                lat=address.lat_wgs84,
                lon=address.long_wgs84,
                label=str(address),
                status=status,
            )
            for address, status in query.limit(100)
        ],
    }


@router.get("/entities/{kennitala}/addresses", response_model=schemas.MapEntityResponse)
async def get_entity_addresses(
    request: Request, kennitala: str, db: Session = Depends(get_db)
):
    entity = _get_entity(db, kennitala)

    most_recent_addresses = (
        db.query(Case.address_id, func.max(Case.updated).label("last_updated"))
        .select_from(Case)
        .join(CaseEntity)
        .filter(CaseEntity.entity == entity)
        .group_by(Case.address_id)
    )
    sq = most_recent_addresses.subquery()

    query = (
        db.query(Address, Case)
        .select_from(Address)
        .join(sq, sq.c.address_id == Address.hnitnum)
        .join(Case, sq.c.last_updated == Case.updated)
        .join(CaseEntity)
        .filter(CaseEntity.entity == entity)
    )

    return {
        "addresses": [
            dict(
                lat=address.lat_wgs84,
                lon=address.long_wgs84,
                label=str(address),
                status=case.status,
            )
            for address, case in query
        ]
    }
