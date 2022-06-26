from typing import Any, List, Optional

from pydantic import BaseModel

from planitor.models import CouncilTypeEnum
from planitor.models.enums import CaseStatusEnum


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
