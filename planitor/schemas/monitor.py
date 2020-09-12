from typing import Optional, Any, List
from pydantic import BaseModel

from planitor.models import CouncilTypeEnum, SubscriptionTypeEnum
from .city import Council, Municipality


class Case(BaseModel):
    id: int
    serial: str
    council: Optional[Council]

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


class SubscriptionCouncilForm(BaseModel):
    selected: bool
    name: str


class SubscriptionForm(BaseModel):
    active: Optional[bool] = None
    immediate: Optional[bool] = None
    radius: Optional[int] = None
    councils: Optional[List[SubscriptionCouncilForm]] = None


class SubscriptionBase(BaseModel):
    active: bool
    immediate: bool
    search_query: Optional[str] = None
    case: Optional[Case] = None
    address: Optional[Address] = None
    radius: Optional[int] = None
    entity: Optional[Entity] = None
    council_types: Optional[List[CouncilTypeEnum]] = None


class Subscription(SubscriptionBase):
    id: int
    type: SubscriptionTypeEnum

    class Config:
        orm_mode = True
