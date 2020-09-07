from typing import Optional, Any
from pydantic import BaseModel


class Case(BaseModel):
    id: int
    serial: str

    class Config:
        orm_mode = True


class Entity(BaseModel):
    kennitala: str
    name: str

    class Config:
        orm_mode = True


class Address(BaseModel):
    hnitnum: int
    name: str = "<Unknown>"

    class Config:
        orm_mode = True


class SubscriptionForm(BaseModel):
    active: Optional[bool] = None
    immediate: Optional[bool] = None
    radius: Optional[int] = None


class SubscriptionBase(BaseModel):
    active: bool
    immediate: bool
    search_query: Optional[str] = None
    case: Optional[Case] = None
    address: Optional[Address] = None
    radius: Optional[int] = None
    entity: Optional[Entity] = None


class Subscription(SubscriptionBase):
    id: int
    type: Any

    class Config:
        orm_mode = True
