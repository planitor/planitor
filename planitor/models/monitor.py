import enum
from collections import namedtuple

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base

EnumValue = namedtuple("EnumValue", ("slug", "label"))


class SubscriptionTypeEnum(enum.Enum):
    case = EnumValue("malsnumer", "Málsnúmer")
    address = EnumValue("heimilisfang", "Heimilisfang")
    street = EnumValue("gata", "Stræti")
    entity = EnumValue("kennitala", "Kennitala")
    radius = EnumValue("radius", "Radíus")
    district = EnumValue("hverfi", "Hverfi")


class Subscription(Base):

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())

    type = Column(Enum(SubscriptionTypeEnum), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")

    address_hnitnum = Column(Integer, ForeignKey("addresses.hnitnum"), nullable=True)
    address = relationship("Address")

    geoname_osm_id = Column(Integer, ForeignKey("geonames.osm_id"), nullable=True)
    geoname = relationship("Geoname")

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    case = relationship("Case")

    entity_kennitala = Column(String, ForeignKey("entities.kennitala"), nullable=True)
    entity = relationship("Entity")


class Letter(Base):
    """ This is kind of a log of emails sent. We don’t want to atomically detect
    items and send them as singular emails, but collate items so that multiple
    items for a single user are collected into one email.

    Using letters, we can run a cron task every 30 minutes, create a time window
    from last letter to the present and send those items.

    """

    __tablename__ = "letters"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    mail_confirmation = Column(String)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")


class Item(Base):

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    subscription = relationship("Subscription")

    minute_id = Column(Integer, ForeignKey("minutes.id"))
    minute = relationship("Minute")

    __table_args__ = (UniqueConstraint("subscription_id", "minute_id"),)
