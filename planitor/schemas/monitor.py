from typing import List, Optional

from pydantic import BaseModel

from planitor.models import CouncilTypeEnum, SubscriptionTypeEnum
from planitor.schemas.enums import EnumChoiceType

from .city import Municipality


class Case(BaseModel):
    id: int
    serial: str
    municipality: Optional[Municipality]

    class Config:
        orm_mode = True


class Entity(BaseModel):
    kennitala: str
    name: str

    class Config:
        orm_mode = True


class Address(BaseModel):
    hnitnum: int
    name: str
    stadur_nf: str
    municipality: Municipality

    class Config:
        orm_mode = True


class SubscriptionBase(BaseModel):
    active: bool
    immediate: bool
    search_query: Optional[str] = None
    case: Optional[Case] = None
    address: Optional[Address] = None
    radius: Optional[int] = None
    entity: Optional[Entity] = None
    council_types: Optional[List[CouncilTypeEnum]] = None


class SubscriptionForm(BaseModel):
    active: Optional[bool] = None
    immediate: Optional[bool] = None
    radius: Optional[int] = None
    council_types: Optional[List[CouncilTypeEnum]] = None


class Subscription(SubscriptionBase):
    id: int
    type: SubscriptionTypeEnum

    class Config:
        orm_mode = True
