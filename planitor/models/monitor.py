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
    district = EnumValue("hverfi", "Hverfi")
    search = EnumValue("leit", "Leit")


class Subscription(Base):

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    active = Column(Boolean, default=True, nullable=False)
    immediate = Column(Boolean, default=True, nullable=False)

    type = Column(Enum(SubscriptionTypeEnum), nullable=False)

    search_query = Column(String)
    search_lemmas = Column(String)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")

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


class Delivery(Base):

    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    sent = Column(Boolean, default=False, nullable=False)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    subscription = relationship("Subscription")

    minute_id = Column(Integer, ForeignKey("minutes.id"))
    minute = relationship("Minute")

    __table_args__ = (UniqueConstraint("subscription_id", "minute_id"),)

    @property
    def _jinja_groupby(self):
        meeting = self.minute.meeting
        return (meeting.start, meeting)
