from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from planitor.database import get_db
from planitor.models import Case, User, Address
from planitor.security import get_current_active_user
from planitor.crud.follow import (
    create_case_subscription,
    delete_case_subscription,
    create_address_subscription,
    delete_address_subscription,
)

router = APIRouter()


@router.post("/cases/{case_id}")
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


@router.delete("/cases/{case_id}")
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


@router.post("/addresses/{hnitnum}")
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


@router.delete("/addresses/{hnitnum}")
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
