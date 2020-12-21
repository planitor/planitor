from decimal import Decimal
import datetime as dt
from typing import Optional

from fastapi import Request
from pydantic import BaseModel

from planitor import models
from planitor.models.enums import BuildingTypeEnum, PermitTypeEnum

from .city import Minute, BaseMunicipality


class PermitBase(BaseModel):
    units: Optional[int]
    area_added: Optional[Decimal]
    area_subtracted: Optional[Decimal]
    building_type: Optional[BuildingTypeEnum]
    permit_type: Optional[PermitTypeEnum]


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


class BaseApiPermit(PermitBase):
    approved: dt.datetime
    url: str
    address: str = None
    postcode: str = None
    municipality: Optional[BaseMunicipality] = None


class ApiLoadPermit(BaseApiPermit):
    def __init__(self, request: Request, permit: models.Permit):
        self.units = permit.units
        self.area_added = permit.area_added
        self.area_subtracted = permit.area_subtracted
        self.building_type = permit.building_type
        self.permit_type = permit.permit_type

        minute = permit.minute
        self.url = request.url_for("get_minute_by_id", id=minute.id)
        self.approved = minute.meeting.start
        self.municipality = BaseMunicipality.from_orm(minute.case.municipality)

        if minute.case.iceaddr:
            case = minute.case
            self.address = str(case.iceaddr)
            self.postcode = str(case.iceaddr.postnr)


def to_camel(string: str) -> str:
    first, *tail = string.split("_")
    return first + "".join(word.capitalize() for word in tail)


class ApiResponsePermit(BaseApiPermit):
    class Config:
        orm_mode = True
        alias_generator = to_camel
        allow_population_by_field_name = True
