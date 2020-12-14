from typing import List

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from planitor.models import enums
from planitor.database import get_db

from . import router


@router.get("/council-types", response_model=List[enums.CouncilTypeEnum])
def get_council_types(
    request: Request,
    db: Session = Depends(get_db),
):
    return list(enums.CouncilTypeEnum)


@router.get("/building-types", response_model=List[enums.BuildingTypeEnum])
def get_building_types(
    request: Request,
    db: Session = Depends(get_db),
):
    return list(enums.BuildingTypeEnum)


@router.get("/permit-types", response_model=List[enums.PermitTypeEnum])
def get_permit_types(
    request: Request,
    db: Session = Depends(get_db),
):
    return list(enums.PermitTypeEnum)
