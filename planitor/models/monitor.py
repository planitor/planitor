import enum
from collections import namedtuple
from reynir import NounPhrase

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
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
    search = EnumValue("leit", "Leit")


class Subscription(Base):

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    active = Column(Boolean, default=True, nullable=False)
    immediate = Column(Boolean, default=True, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")

    type = Column(Enum(SubscriptionTypeEnum), nullable=False)

    search_query = Column(String)
    search_lemmas = Column(String)

    address_hnitnum = Column(Integer, ForeignKey("addresses.hnitnum"), nullable=True)
    address = relationship("Address")
    radius = Column(Integer)

    geoname_osm_id = Column(Integer, ForeignKey("geonames.osm_id"), nullable=True)
    geoname = relationship("Geoname")

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    case = relationship("Case")

    entity_kennitala = Column(String, ForeignKey("entities.kennitala"), nullable=True)
    entity = relationship("Entity")

    def get_string(self, case="nominative"):
        if self.type == SubscriptionTypeEnum.case:
            nl = "málsnúmeri {}".format(self.case.serial)
        elif self.type == SubscriptionTypeEnum.address:
            nl = str(self.address)
        elif self.type == SubscriptionTypeEnum.entity:
            nl = self.entity.name
        elif self.type == SubscriptionTypeEnum.radius:
            nl = NounPhrase(str(self.address))
            return "{nl:þgf} með {radius}m radíus".format(nl=nl, radius=self.radius)
        elif self.type == SubscriptionTypeEnum.search:
            nl = "leitinni '{}'".format(self.search_query)
        else:
            raise NotImplementedError
        return "{0:þgf}".format(NounPhrase(nl))


class Delivery(Base):

    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    sent = Column(DateTime)
    mail_confirmation = Column(String)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    subscription = relationship("Subscription")

    deleted_subscription_id = Column(Integer)
    deleted_user_id = Column(Integer)

    minute_id = Column(Integer, ForeignKey("minutes.id"), nullable=False)
    minute = relationship("Minute")

    __table_args__ = (UniqueConstraint("subscription_id", "minute_id"),)

    @property
    def _jinja_groupby(self):
        meeting = self.minute.meeting
        return (meeting.start, meeting)
