from typing import List, Any
from pydantic import BaseModel

from planitor.models import CouncilTypeEnum


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
