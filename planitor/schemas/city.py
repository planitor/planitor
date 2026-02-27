import datetime as dt
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

from planitor.models import CouncilTypeEnum
from planitor.models.enums import CaseStatusEnum

T = TypeVar("T")


class BaseCouncil(BaseModel):
    id: int
    name: str
    council_type: CouncilTypeEnum

    class Config:
        orm_mode = True


class BaseMunicipality(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class Council(BaseCouncil):
    municipality: BaseMunicipality

    class Config:
        orm_mode = True


class Municipality(BaseMunicipality):
    councils: List[BaseCouncil] = []

    class Config:
        orm_mode = True


class Minute(BaseModel):
    id: int

    class Config:
        orm_mode = True


class PlanPolygon(BaseModel):
    plan: Any
    polygon: Any


class MapAddress(BaseModel):
    lat: float
    lon: float
    label: str
    status: Optional[CaseStatusEnum]


class MapCasesResponse(BaseModel):
    plan: Optional[PlanPolygon]
    address: MapAddress
    addresses: List[MapAddress]


class MapEntityResponse(BaseModel):
    addresses: List[MapAddress]


# Explore API schemas


class ExploreAddress(BaseModel):
    heiti_nf: Optional[str]
    husnr: Optional[int]
    lat: Optional[float]
    lon: Optional[float]
    label: str

    class Config:
        orm_mode = True


class ExploreEntity(BaseModel):
    kennitala: str
    name: Optional[str]

    class Config:
        orm_mode = True


class ExploreMinute(BaseModel):
    id: int
    headline: str
    inquiry: Optional[str]
    remarks: Optional[str]
    status: Optional[CaseStatusEnum]
    meeting_date: dt.date
    council: str
    case_serial: Optional[str]
    case_address: Optional[str]

    class Config:
        orm_mode = True


class ExploreCase(BaseModel):
    id: int
    serial: str
    address: Optional[str]
    status: Optional[CaseStatusEnum]
    updated: Optional[dt.datetime]
    lat: Optional[float]
    lon: Optional[float]
    council_type: Optional[CouncilTypeEnum]

    class Config:
        orm_mode = True


class ExploreCaseDetail(ExploreCase):
    minutes: List[ExploreMinute]


class PaginatedResponse(GenericModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
