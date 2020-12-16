from typing import List

from fastapi import Depends, Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from planitor import models
from planitor.database import get_db
from planitor.models.enums import BuildingTypeEnum, PermitTypeEnum
from planitor.schemas.permits import (
    Permit,
    PermitForm,
)
from planitor.permits import PermitMinute
from planitor.security import get_current_active_superuser

from . import router


@router.get("/minutes/{minute_id}/permit", response_model=Permit)
def get_permit(
    request: Request,
    minute_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser),
):
    minute = db.query(models.Minute).get(minute_id)
    if minute is None:
        raise HTTPException(404)
    permit = minute.permit
    if permit is None:
        permit = PermitMinute(minute)
    return permit


@router.put("/minutes/{minute_id}/permit", response_model=Permit)
def update_permit(
    request: Request,
    minute_id: int,
    form: PermitForm,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser),
):
    minute = db.query(models.Minute).get(minute_id)
    if minute is None:
        raise HTTPException(404)
    permit = minute.permit
    if permit is None:
        permit = models.Permit(minute=minute)

    permit.units = form.units
    permit.area_added = form.area_added
    permit.area_subtracted = form.area_subtracted

    permit.building_type = None
    permit.permit_type = None
    if form.building_type:
        permit.building_type = getattr(BuildingTypeEnum, form.building_type)
    if form.permit_type:
        permit.permit_type = getattr(PermitTypeEnum, form.permit_type)

    db.add(permit)
    db.commit()
    db.refresh(permit)
    return permit
