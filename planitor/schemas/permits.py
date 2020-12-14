from decimal import Decimal
import datetime as dt
from typing import Optional

from pydantic import BaseModel

from planitor.models.enums import BuildingTypeEnum, PermitTypeEnum

from .city import Minute


class PermitBase(BaseModel):
    units: Optional[int] = None
    area_added: Optional[Decimal] = None
    area_subtracted: Optional[Decimal] = None
    building_type: Optional[BuildingTypeEnum] = None
    permit_type: Optional[PermitTypeEnum] = None


class Permit(PermitBase):
    minute: Optional[Minute] = None
    created: Optional[dt.datetime] = None

    class Config:
        orm_mode = True


class PermitForm(PermitBase):
    """Can't use enums here because Pydantic does not support validating based on
    enum name and not value. If we hack it to support that via a validate decorator
    that in turn breaks other things (the -types endpoints)"""

    building_type: Optional[str] = None
    permit_type: Optional[str] = None
