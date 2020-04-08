import enum
from collections import namedtuple

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import ARRAY, BIGINT, TEXT, NUMERIC
from sqlalchemy_utils import CompositeArray, CompositeType

from .utils.kennitala import Kennitala
from .database import Base

EnumValue = namedtuple("EnumValue", ("slug", "label"))

ColorEnumValue = namedtuple("ColorEnumValue", ("slug", "label", "color"))


class CouncilTypeEnum(enum.Enum):
    byggingarfulltrui = EnumValue("byggingarfulltrui", "Byggingarfulltrúi")
    skipulagsfulltrui = EnumValue("skipulagsfulltrui", "Skipulagsfulltrúi")
    skipulagsrad = EnumValue("skipulagsrad", "Skipulagsráð")
    borgarrad = EnumValue("borgarrad", "Borgarráð")
    borgarstjorn = EnumValue("borgarstjorn", "Borgarstjórn")


class PlanTypeEnum(enum.Enum):
    deiliskipulag = EnumValue("deiliskipulag", "Deiliskipulag")
    adalskipulag = EnumValue("adalskipulag", "Aðalskipulag")
    svaedisskipulag = EnumValue("svaedisskipulag", "Svæðisskipulag")


class EntityTypeEnum(enum.Enum):
    person = EnumValue("persona", "Persóna")
    company = EnumValue("fyrirtaeki", "Fyrirtæki")


class CaseStatusEnum(enum.Enum):
    approved = ColorEnumValue("samthykkt", "Samþykkt", "green")
    answered_positive = ColorEnumValue("jakvaett", "Jákvætt", "green")
    delayed = ColorEnumValue("frestad", "Frestað", "yellow")

    notice = ColorEnumValue("grenndarkynning", "Samþykkt að grenndarkynna", "yellow")

    directed_to_skipulagsrad = ColorEnumValue(
        "visad-til-skipulags", "Vísað til Skipulags- og samgönguráðs", "yellow"
    )
    directed_to_adalskipulag = ColorEnumValue(
        "visad-til-deildarstjora-adalskipulags",
        "Vísað til umsagnar deildarstjóra aðalskipulags",
        "yellow",
    )
    assigned_project_manager = ColorEnumValue(
        "visad-til-verkefnastjora", "Vísað til verkefnisstjóra", "yellow"
    )
    answered_negative = ColorEnumValue("neikvaett", "Neikvætt", "red")
    denied = ColorEnumValue("neitad", "Synjað", "red")
    no_comment = ColorEnumValue("engar-athugasemdir", "Engar athugasemdir", "blue")


class Geoname(Base):
    __tablename__ = "geonames"
    osm_id = Column(BIGINT, primary_key=True, index=True, autoincrement=False)
    name = Column(TEXT)
    lon = Column(Numeric)
    lat = Column(Numeric)
    place_rank = Column(Integer)
    city = Column(TEXT)
    importance = Column(NUMERIC)
    alternative_names = Column(TEXT)
    class_ = Column("class", TEXT)
    country = Column(TEXT)
    country_code = Column(TEXT)
    county = Column(TEXT)
    display_name = Column(TEXT)
    housenumbers = Column(TEXT)
    osm_type = Column(TEXT)
    state = Column(TEXT)
    street = Column(TEXT)
    type_ = Column("type", TEXT)
    wikidata = Column(TEXT)
    wikipedia = Column(TEXT)

    east = Column(NUMERIC)
    north = Column(NUMERIC)
    south = Column(NUMERIC)
    west = Column(NUMERIC)


class Housenumber(Base):
    __tablename__ = "housenumbers"
    osm_id = Column(BIGINT, primary_key=True, index=True, autoincrement=False)
    street_name = Column("street", TEXT)
    lon = Column(Numeric)
    lat = Column(Numeric)
    housenumber = Column(TEXT)

    street_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    street = relationship(Geoname)


class Entity(Base):
    # As in "legal entity"; person or company
    __tablename__ = "entities"

    kennitala = Column(String, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)
    slug = Column(String)
    website_url = Column(String, nullable=True)
    entity_type = Column(Enum(EntityTypeEnum))
    address = Column(String, nullable=True)
    birthday = Column(Date)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id), nullable=True)
    geoname = relationship(Geoname)

    def get_human_kennitala(self):
        return "{}-{}".format(self.kennitala[:6], self.kennitala[6:])


class Municipality(Base):
    __tablename__ = "municipalities"
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)
    slug = Column(String, unique=True, nullable=False)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    geoname = relationship(Geoname)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created = Column(DateTime, server_default=func.now())

    parent_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    parent = relationship("Plan", remote_side=[id])

    minicipality_id = Column(Integer, ForeignKey(Municipality.id))
    minicipality = relationship(Municipality)


class Council(Base):
    __tablename__ = "councils"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)
    active = Column(Boolean, default=True)

    municipality_id = Column(Integer, ForeignKey(Municipality.id), nullable=True)
    municipality = relationship(Municipality)

    council_type = Column(Enum(CouncilTypeEnum))


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created = Column(DateTime, server_default=func.now())
    start = Column(DateTime, nullable=False)
    end = Column(DateTime)
    description = Column(String)
    attendant_names = Column(ARRAY(String))
    url = Column(String)

    council_id = Column(Integer, ForeignKey(Council.id))
    council = relationship(Council)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    file_url = Column(String)
    file_type = Column(String, nullable=True)
    name = Column(String)


class Tag(Base):
    __tablename__ = "tags"
    name = Column(String, primary_key=True, index=True)


class CaseEntity(Base):
    __tablename__ = "case_entities"
    entity_id = Column(String, ForeignKey("entities.kennitala"), primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), primary_key=True)
    applicant = Column(Boolean, default=True)
    entity = relationship(Entity)

    # It’s a bit weird that minutes contribute entities to cases. If we update the
    # inquiry field and re-assess the entities mentioned of a minute we cannot remove
    # an entity no longer in the minute because another minute of the same case could
    # have contributed it. This should be ok since inquiries never change.


class CaseAttachment(Base):
    # We want to collate all attachments to cases, but they can be associated with a
    # meeting minute about a case where they first appeared
    __tablename__ = "case_attachments"
    attachment_id = Column(Integer, ForeignKey("attachments.id"), primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), primary_key=True)
    created = Column(DateTime, server_default=func.now())

    minute_id = Column(Integer, ForeignKey("minutes.id"))
    minute = relationship("Minute")


class CaseTag(Base):
    # We want to collate all tags to cases, but they can be associated with a
    # meeting minute about a case where they first appeared
    __tablename__ = "case_tags"
    tag_id = Column(String, ForeignKey("tags.name"), primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), primary_key=True)
    approved = Column(
        Boolean, default=False
    )  # We want to process suggested tags approved by an admin

    minute_id = Column(Integer, ForeignKey("minutes.id"))
    minute = relationship("Minute")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String)
    created = Column(DateTime, server_default=func.now())
    address = Column(String)

    # This field is denormalized, is derived from most recent minute
    status = Column(Enum(CaseStatusEnum), nullable=True)
    updated = Column(DateTime, nullable=True)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    geoname = relationship(Geoname)

    housenumber_osm_id = Column(BIGINT, ForeignKey(Housenumber.osm_id))
    housenumber = relationship(Housenumber)

    council_id = Column(Integer, ForeignKey(Council.id))
    council = relationship(Council)

    # This case could relate to a deiliskipulag
    plan_id = Column(Integer, ForeignKey(Plan.id))
    plan = relationship(Plan)

    attachments = relationship(CaseAttachment)
    tags = relationship(CaseTag)
    entities = relationship(CaseEntity)

    __table_args__ = (UniqueConstraint("serial", "council_id"),)

    def get_coordinates(self):
        if self.housenumber_osm_id:
            return self.housenumber.lat, self.housenumber.lon
        if self.geoname_osm_id:
            return self.geoname.lat, self.geoname.lon


class EntityMention(object):
    """ Used to mark parsed company names inside the inquiry text property. Very
    expensive to calculate on the fly, so we store it here.

    """

    def __init__(self, entity, start, stop):
        self.entity = entity
        self.start = start
        self.stop = stop

    def __composite_values__(self):
        return self.entity, self.start, self.stop

    def __repr__(self):
        return "EntityMention(entity={}, start={}, stop={})".format(
            self.entity.id, self.start, self.stop
        )

    def __eq__(self, other):
        return (
            isinstance(other, EntityMention)
            and other.entity == self.entity
            and other.start == self.start
            and other.stop == self.stop
        )


class Minute(Base):
    __tablename__ = "minutes"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String, index=True)
    case_id = Column(Integer, ForeignKey(Case.id), nullable=True)
    case = relationship(Case)
    status = Column(Enum(CaseStatusEnum), nullable=True)
    meeting_id = Column(Integer, ForeignKey(Meeting.id), nullable=True)
    meeting = relationship(Meeting)
    headline = Column(String)
    inquiry = Column(String)
    remarks = Column(String)
    entity_mentions = Column(
        CompositeArray(
            CompositeType(
                "entity_mention_type",
                [
                    Column("entity_id", String, ForeignKey(Entity.kennitala)),
                    Column("start", Integer),
                    Column("end_", Integer),
                ],
            )
        )
    )

    def assign_entity_mentions(self, mentions):
        self.entity_mentions = []
        for kennitala, locations in mentions.items():
            for location in locations:
                start, end = location
                self.entity_mentions.append((kennitala, start, end))

    def get_inquiry_mention_tokens(self):
        """ Use `entity_mentions` to mark linkable locations in the `inquiry` text
        """
        s = self.inquiry
        mentions = sorted(self.entity_mentions, key=lambda i: i[1])
        for i, (kennitala, start, end) in enumerate(mentions):
            if i == 0 and start > 0:
                yield (None, s[0:start])
            elif i > 0:
                last = mentions[i - 1]
                yield (None, s[last[1] + 1 : start])
            yield (Kennitala(kennitala), s[start:end])
            last_index = len(mentions) - 1
            if i == last_index and end != len(s):
                yield (None, s[end:])
        if not mentions:
            yield (None, s)
