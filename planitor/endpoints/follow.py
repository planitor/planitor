from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from planitor.database import get_db
from planitor.models import Case, User
from planitor.security import get_current_active_user
from planitor.crud.follow import create_case_subscription, delete_case_subscription

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
