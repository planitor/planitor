from fastapi import Depends, Request, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import datetime as dt

from planitor.models import Address, Case, CaseEntity
from planitor.database import get_db

from ..utils import _get_entity
from . import router


@router.get("/addresses/{hnitnum}/addresses")
async def get_nearby_case_addresses(
    request: Request,
    hnitnum: int,
    radius: int = 500,
    days: int = 30,
    db: Session = Depends(get_db),
):
    address = db.query(Address).filter(Address.hnitnum == hnitnum).first()
    if address is None:
        return HTTPException(404)

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

    return {
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


@router.get("/entities/{kennitala}/addresses")
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
