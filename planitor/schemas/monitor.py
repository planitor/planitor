from typing import Optional
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
    name: str

    class Config:
        orm_mode = True


class SubscriptionForm(BaseModel):
    active: bool
    immediate: bool


class SubscriptionBase(BaseModel):
    active: bool
    immediate: bool
    search_query: Optional[str] = None
    case: Optional[Case] = None
    address: Optional[Address] = None
    radius: Optional[int] = None
    entity: Optional[Entity] = None


class Subscription(SubscriptionBase):
    id: int = None

    class Config:
        orm_mode = True
