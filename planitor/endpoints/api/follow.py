from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from planitor.database import get_db
from planitor.models import Case, User, Address, Entity
from planitor.security import get_current_active_user
from planitor.crud.follow import (
    create_case_subscription,
    delete_case_subscription,
    create_entity_subscription,
    delete_entity_subscription,
    create_address_subscription,
    delete_address_subscription,
)

from . import router


@router.post("/follow/cases/{case_id}")
async def follow_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case = db.query(Case).get(case_id)
    if case is None:
        return HTTPException(404)
    create_case_subscription(db, current_user, case)
    return {}


@router.delete("/follow/cases/{case_id}")
async def unfollow_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case = db.query(Case).get(case_id)
    if case is None:
        return HTTPException(404)
    delete_case_subscription(db, current_user, case)
    return {}


@router.post("/follow/entities/{kennitala}")
async def follow_entity(
    kennitala: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = db.query(Entity).get(kennitala)
    if entity is None:
        return HTTPException(404)
    create_entity_subscription(db, current_user, entity)
    return {}


@router.delete("/follow/entities/{kennitala}")
async def unfollow_entity(
    kennitala: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = db.query(Entity).get(kennitala)
    if entity is None:
        return HTTPException(404)
    delete_entity_subscription(db, current_user, entity)
    return {}


@router.post("/follow/addresses/{hnitnum}")
async def follow_address(
    hnitnum: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    address = db.query(Address).get(hnitnum)
    if address is None:
        return HTTPException(404)
    create_address_subscription(db, current_user, address)
    return {}


@router.delete("/follow/addresses/{hnitnum}")
async def unfollow_address(
    hnitnum: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    address = db.query(Address).get(hnitnum)
    if address is None:
        return HTTPException(404)
    delete_address_subscription(db, current_user, address)
    return {}
